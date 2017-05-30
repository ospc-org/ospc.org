# PUF package

A private Anaconda package for Public Use File (PUF)

## Preliminary

### *No accidental uploads!*
Make sure you never automatically upload this package to your personal
account:

`conda config --set anaconda_upload no`

### Use Anaconda Token

Get the *general* Anaconda upload token from me (Peter S) and save it in a one-line text file in your home directory with this file name:

`.ospc_anaconda_token`

Get the `conda:download` only Anaconda token from me (Peter S) and save it in a one-line text file in your home directory with this file name:

`.ospc_anaconda_token_conda_download`


## Get the PUF package builder

I made a script that will automate creating a new package `puf` for a new `puf.csv` file.  To get the helper, download the private Anaconda pakcage `puf_builder`:

```
mkdir puf_work && cd puf_work
anaconda --token ~/.ospc_anaconda_token download opensourcepolicycenter/puf_builder
```
The above downloads the builder using the token for privacy.  Then unzip the file you got:
```
unzip puf_builder.zip
```
Next run `build_puf_package.py` script with 3 arguments:
 * Path to the new `puf.csv` you want in the new `puf` package
 * A note about the new `puf.csv` (quotes around it if spaces in note)
 * The new `puf` package's version, such as 0.0.0

```
python build_puf_package.py abc.txt "testing it out" 0.0.4
```
That will `conda build` the `puf` package after copying your new puf.csv into it, then upload packages to Anaconda under the private package:

`opensourcepolicycenter/puf`

## Make sure your new version was uploaded

Check and make sure you have a `conda` type of package for the version you just created, for each of the major platforms:

https://anaconda.org/opensourcepolicycenter/puf

## Instaling the `puf` package

Assuming you have saved the tokens mentioned at top of this page:

```
export TOKEN=`cat ~/.ospc_anaconda_token_conda_download`
conda install -c https://conda.anaconda.org/t/$TOKEN/opensourcepolicycenter puf
python -c "from puf import PUF, PUF_META, PUF_VERSION"

```
