# Establishing Facts: the numbers, rechecked

This repository lets anyone rerun the numbers in the free book *Establishing Facts: Statistics, the Scientific Method, and Your Own Research*, by Nicholas Elliott Karlson (NEKpress Research: Proof-First Guides, Version 1.0).

The book is free on Zenodo, under CC BY 4.0, in the NEKpress Research community: https://zenodo.org/communities/nekpress.

It holds only what that takes:

- the three programs that recompute the book's numbers;
- the ledger, which lists the source of every number the book prints;
- a copy of the Tonmick files the programs read. These are taken unchanged from the Predictive companion, release v1.0.1, and listed with the companion's own checksums.

## Rerun the numbers

You need Python 3.10 or later and Git. These are the commands the book prints, in its back matter ("Where the Numbers Come From"):

```
git clone https://github.com/nicholaskarlson/facts.git
cd facts
python3 verification/independent/spine_check.py companion
python3 verification/independent/details_check.py companion
python3 verification/independent/chapter_numbers_check.py companion
```

On Windows, type `python` in place of `python3`. If you don't have Git, choose **Code**, then **Download ZIP** on this page. Unzip the file, and run the last three commands in the folder it makes.

Each program ends with one line:

```
SPINE_CHECK_OK values=65
DETAILS_CHECK_OK values=41
CHAPTER_NUMBERS_OK values=35
```

Anything else is a mismatch between the files and the book. Please report it, with the page and the sentence, through https://nekpress.ca or as an issue here.

The programs use only the Python standard library, so there is nothing to install. They share no code with the companion.

## What each program checks

| Program | What it recomputes | Where the book prints it |
| --- | --- | --- |
| `spine_check.py` | The Tonmick mentoring trial: who was offered mentoring, who withdrew, the difference and its interval, the Bayesian figures, power, and the worked decision with its invented costs | Chapters 3, 6, 8, 12, and 18, and the answers to Chapter 3's exercise |
| `details_check.py` | More of the same files: who joined, the entry survey's two scales, support visits, grades in the 16 colleges, and regression to the mean | Chapters 12 to 15, and 17 |
| `chapter_numbers_check.py` | The numbers the book works out for itself: the coin, the birthdays, the screening test, Maya's and Sam's beliefs, and the exercises | Chapters 2 and 20, and the exercises in Chapters 5 to 8 and 10, with their answers |

Each program compares every value it computes with the number the book prints, and stops with a list of differences if any value disagrees. When the book itself is built, the same programs also check that every sentence printing one of these numbers is still in the text. That check needs the book's source, so this copy, which holds no book text, checks the values only.

## What is here

```
verification/independent/   the three programs
verification/ledger.csv     every number in the book: where it is printed, its source, and its check
companion/                  the Tonmick files the programs read, at the Predictive companion's own paths
```

The ledger's columns are:

- the number as printed;
- the chapter and section;
- the source (a record and section, a page, or a computation);
- the companion file;
- the program and value that check it.

Numbers from the series' free records and from published works are printed as their sources print them, and the ledger says where.

## Where the files come from

The files under `companion/` are copied byte for byte from https://github.com/nicholaskarlson/predict, release v1.0.1 (commit `24d1023`). `companion/SHA256SUMS` repeats the companion's own checksums for exactly these files. To confirm that your copy matches, run one of these:

```
cd companion && sha256sum -c SHA256SUMS          # Linux
cd companion && shasum -a 256 -c SHA256SUMS      # macOS
```

The data are synthetic: Tonmick is a fictional college system made by a program that follows written rules. `WORLD_SPEC.md` gives those rules. The book cites it when it compares an estimate with the truth.

The automated checks on this repository run all three programs, as printed, on Ubuntu, macOS, and Windows.

## License

- **Programs:** MIT License (`LICENSE-CODE`).
- **Ledger and this README:** CC BY 4.0, like the book.
- **Files under `companion/`:** keep their own licenses (CC BY 4.0 for the data and documentation), stated in the `LICENSES.md` beside them.

Copyright © 2026 Nicholas Elliott Karlson. No license here covers the NEKpress name, the series name and branding, or any cover art.
