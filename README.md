# SMM2
Bunch of utils for dealing with SMM2 level formats for "kAIzo"

## Requirements
1. https://github.com/simontime/SMM2CourseDecryptor
	- clone & build with `gcc -o smm2cd main.c aes.c -lmbedtls -lmbedx509 -lmbedcrypto`

## Usage
`python level_gen.py course_data_000.bcd`

## Credits
Thanks to https://github.com/Treeki/SMM2Reversing & https://github.com/0Liam/smm2-documentation for providing level format info
