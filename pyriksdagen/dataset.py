from transformers import BertTokenizerFast
import torch

class IntroDataset(torch.utils.data.Dataset):
    ''' Dataset for predicting introductions '''
    def __init__(self, df):
        self.df = df
        self.tokenizer = BertTokenizerFast.from_pretrained('KB/bert-base-swedish-cased')

    def __len__(self):
        return len(self.df)

    def __getitem__(self, index):

        df_row = self.df.iloc[index]
        token_info = self.tokenizer.encode_plus(
                                            df_row['text'],                       # Sentence to encode.
                                            add_special_tokens = True,      # Add '[CLS]' and '[SEP]'
                                            max_length = 50,                # Pad & truncate all sentences.
                                            padding='max_length',
                                            truncation=True,
                                            return_attention_mask = True,   # Construct attn. masks.
                                            return_tensors = 'pt',          # Return pytorch tensors.
                                            )

        return token_info, df_row['id'], df_row['file_path']