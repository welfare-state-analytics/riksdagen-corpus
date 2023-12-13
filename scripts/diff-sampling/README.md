# Diff sampling

When we make changes to data, we take a sample of edits to check whether they in fact do what we intend. This is accomplished by taking a random sample of the diffs and posting for quality controll before commiting and pushing changes with many edits to the repo.

There is sometimes utility in dumping the whole diff to a local file for in depth exploration, manually or using `scripts/diff-sampling/diff-search.py`


# General procedure

Use the [sample-git-diffs](https://pypi.org/project/sample-git-diffs/) tool to generate a sample of changes made to the corpus data.

```
sample-git-diffs --diffstat "git diff --stat -- corpus/protocols" --n 50 > <path/to/.diff-file>
```

### diff-to-markdown

Create a markdown file:

```
diff2markdown --path <path/to/.diff-file> --username <of/repo> --repo <repo> --branch <branch> > <path/to/.md-file>
```

### git add the sample

Git add _only_ the files sampled

```
python scripts/diff-sampling/git-add_diff-sample.py
```

* commit and push
* check links in markdown work
* open PR
* post sample.md in the comment
* use git stash to save uncommited changes until the posted sample is deemed OK, then pop+add+commit