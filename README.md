# SMM2
Bunch of utils for dealing with SMM2 level formats

Built primarily for working on "[kAIzo](https://github.com/pifalken/kAIzo)" (generating SMM2 kaizo levels using LMs, RNNs, and VAEs)

## Requirements
1. https://github.com/simontime/SMM2CourseDecryptor
	- clone & build with `gcc -o smm2cd main.c aes.c -lmbedtls -lmbedx509 -lmbedcrypto`

## Usage
`python level_gen.py course_data_000.bcd`

## Example
- example 000:
![example000]

[example000]: https://github.com/pifalken/SMM2/raw/master/other/level_gen_example_000.png

## Credits
Thanks to https://github.com/Treeki/SMM2Reversing & https://github.com/0Liam/smm2-documentation for providing level format info
