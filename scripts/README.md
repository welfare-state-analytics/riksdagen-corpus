# Scripts


## Description of functionality

### `query2csv.py`

This will generate an input csv file from a query of kblab's protocol packages, e.g. a range of years. You can also set the `-m | --mkdirs` flag to make directories corresponding to the query years in `corpus/protocols/`


## How to...

### How to use scripts in general

#### Running the scripts

Scripts are necessarily run from project root.

To be able to run the scripts from the project root, either (A) prepend it with defining PYTHONPATH in the following way

```PYTHONPATH="$PYTHONPATH:." python scripts/resegment.py```

or (B) install `pyriksdagen` in the python venv, e.g. by

```cp -R pyriksdagen ../mykblenv/lib/python<version>/site-packages/```

Strategy (B) would need to be repeated after any changes to pyriksdagen, as they wouldn't be automatically propagated to the venv (since these ought to be outside any git tracking).



#### LazyArchive

The LazyArchive() class attempts to connect to the KB labs in the lazyest way possible. If you'll use the scripts often, it's worthwhile to set 3 environment variables 

	KBLMYLAB=https://betalab.kb.se
	KBLUSER=
	KBLPASS=

If these are not present, you will be prompted for the username and password.



### How to use the scripts to curate data

(Steps are added as we go)

1. Generate an input csv by querying protocol packages using `query2csv.py`




