import numpy as np
import pandas as pd
from transformers import AutoModel, AutoTokenizer, AutoModelForSequenceClassification
import torch
import torch.nn as nn
from torch.utils.data import TensorDataset, random_split, DataLoader
from transformers import get_linear_schedule_with_warmup
import argparse
from tqdm import tqdm
import os


def encode(df):
	tokenizer = AutoTokenizer.from_pretrained('KBLab/bert-base-swedish-cased')

	# Tokenize all of the sentences and map the tokens to thier word IDs.
	input_ids = []
	attention_masks = []

	# For every sentence...
	for _, row in df.iterrows():
	    encoded_dict = tokenizer.encode_plus(
	                        row['content'],                      
	                        add_special_tokens = True,
	                        max_length = 512,
	                        truncation=True,
	                        padding = 'max_length',
	                        return_attention_mask = True,
	                        return_tensors = 'pt',
	                   )
	    
	    # Add the encoded sentence to the list.    
	    input_ids.append(encoded_dict['input_ids'])
	    
	    # And its attention mask (simply differentiates padding from non-padding).
	    attention_masks.append(encoded_dict['attention_mask'])

	# Convert the lists into tensors.
	input_ids = torch.cat(input_ids, dim=0)
	attention_masks = torch.cat(attention_masks, dim=0)
	labels = torch.tensor(df['tag'].tolist())

	return input_ids, attention_masks, labels


def predict(model, loader):
	loss = 0
	preds = []
	model.eval()
	for batch in tqdm(loader, total=len(loader)):
		input_ids = batch[0].to(args.device)
		input_mask = batch[1].to(args.device)
		labels = batch[2].to(args.device)
		output = model(input_ids,
			token_type_ids=None, 
			attention_mask=input_mask, 
			labels=labels)
		loss += output.loss.item()
		preds.extend(torch.argmax(output.logits, axis=1).tolist())
	return loss, preds


def main(args):	
	df = pd.read_csv('input/multi_label_classifier/training_data.csv')
	df = df.sample(frac=1, random_state=123).reset_index(drop=True)

	# Create binary label where seg = 1
	df['tag'] = np.where(df['seg'] == 1, 1, 0)

	# Preprocess datasets
	input_ids, attention_masks, labels = encode(df)

	dataset = TensorDataset(input_ids, attention_masks, labels)
	train_size	= int(args.train_ratio * len(dataset))
	val_size	= int(args.valid_ratio * len(dataset))
	test_size	= len(dataset) - train_size - val_size
	train_dataset, valid_dataset, test_dataset = random_split(dataset, [train_size, val_size, test_size])

	train_loader = DataLoader(
            train_dataset,
            shuffle=True,
            batch_size = 16,
            num_workers = args.num_workers
        )

	valid_loader = DataLoader(
            valid_dataset,
            shuffle=False,
            batch_size = 16,
            num_workers = args.num_workers
        )

	# Not used atm
	test_loader = DataLoader(
            test_dataset,
            shuffle=False,
            batch_size = 16,
            num_workers = args.num_workers
        )

	model = AutoModelForSequenceClassification.from_pretrained(
		'KBLab/bert-base-swedish-cased',
		num_labels=2).to(args.device)

	# Initialize optimizer
	loss_fn = nn.BCEWithLogitsLoss()
	optimizer = torch.optim.Adam(
		filter(lambda p: p.requires_grad, model.parameters()), lr=args.learning_rate)
	num_training_steps = len(train_loader) * args.n_epochs
	num_warmup_steps = num_training_steps // 10

	# Linear warmup and step decay
	scheduler = get_linear_schedule_with_warmup(
		optimizer = optimizer,
		num_warmup_steps = num_warmup_steps,
		num_training_steps = num_training_steps
		)


	train_losses = []
	valid_losses = []
	best_valid_loss = float('inf')
	os.environ["TOKENIZERS_PARALLELISM"] = "false"

	for epoch in range(args.n_epochs):
		train_loss = 0
		model.train()
		for batch in tqdm(train_loader, total=len(train_loader)):
			model.zero_grad()	

			input_ids = batch[0].to(args.device)
			input_mask = batch[1].to(args.device)
			labels = batch[2].to(args.device)
			output = model(input_ids,
				token_type_ids=None, 
				attention_mask=input_mask, 
				labels=labels)
			loss = output.loss
			train_loss += loss.item()

			loss.backward()
			optimizer.step()
			scheduler.step()

		# Evaluation
		valid_loss, preds = predict(model, valid_loader)

		train_losses.append(train_loss)
		valid_losses.append(valid_loss)
		print(f'Training Loss: {train_loss:.3f}')
		print(f'Validation Loss: {valid_loss:.3f}')

		labels = df.loc[valid_dataset.indices, 'tag'].tolist()		
		print(f'Eval accuracy: {sum([x==y for x, y in zip(labels, preds)]) / len(labels)}')

        # Store best model
        if valid_loss < best_valid_loss:
        	best_valid_loss = valid_loss
            torch.save({
                'epoch': epoch+1,
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'loss': loss_fn,
                }, args.model_filename)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model_filename", type=str, default="input/multi_label_classifier/binary_note_seg_model.pth")
    parser.add_argument("--device", type=str, default="cuda")
    parser.add_argument("--n_epochs", type=int, default=10)
    parser.add_argument("--batch_size", type=int, default=16)
    parser.add_argument("--num_workers", type=int, default=4)
    parser.add_argument("--learning_rate", type=float, default=0.00002)
    parser.add_argument("--train_ratio", type=float, default=0.6)
    parser.add_argument("--valid_ratio", type=float, default=0.2) # test set is what remains after train and valid splits
    args = parser.parse_args()
    main(args)
