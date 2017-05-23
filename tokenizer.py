# encoding: utf-8
import re
import snowballstemmer
import sqlitefts as fts


class SnowballRussianTokenizer(fts.Tokenizer):
    name = 'snowball_russian'
    split_pattern = re.compile(r'\w+', re.UNICODE)
    stemmer = snowballstemmer.stemmer('russian')

    def tokenize(self, text):
        """
        Tokenize given unicode text. Yields each tokenized token,
        start position(in bytes), end position (in bytes)
        """

        for match in self.split_pattern.finditer(text):
            start, end = match.span()
            token = text[start:end].lower()
            stemmed = self.stemmer.stemWord(token)
            length = len(token.encode('utf-8'))
            pos = len(text[:start].encode('utf-8'))
            print stemmed, pos, pos + length
            yield stemmed, pos, pos + length


def register_tokenizer(sqlite_connection):
    tokenizer_module = fts.make_tokenizer_module(SnowballRussianTokenizer())
    fts.register_tokenizer(sqlite_connection, SnowballRussianTokenizer.name, tokenizer_module)
