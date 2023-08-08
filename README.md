Raw samples are in the `raw` directory. The directory structure here is based on whatever was easiest for me when I was recording and saving the audio.

The `tagged` directory contains a copy of `raw` that is easier to programmatically process. It is excluded by the `.gitignore` since it's generated deterministically as a function of `raw`.

Run the following to generate the `tagged` directory:

```
make
```
