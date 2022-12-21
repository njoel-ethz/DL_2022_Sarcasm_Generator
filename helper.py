"""
    Helper functions for sarcasm classic_finetuned
"""
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split


def preprocessing(df, field):
    # Remove @...
    df[field] = df[field].replace(regex=['(@\w+)'], value='')
    # Remove <URL>
    df[field] = df[field].replace(regex=['<URL>'], value='')
    # Remove links
    df[field] = df[field].replace(regex=['(https?:\/\/)?([\da-z\.-]+)\.([a-z\.]{2,6})([\/\w\.-]*)'], value='')
    # Remove multiple spaces
    df[field] = df[field].replace(regex=['  +'], value=' ')
    # Remove emojis
    df[field] = df[field].apply(lambda s: ''.join(filter(lambda c: ord(c) < 256, s)))
    # Remove leading and trailing spaces
    df[field] = df[field].str.strip()
    # Drop empty columns
    df[field].replace('', np.nan, inplace=True)
    df.dropna(subset=[field], inplace=True)
    return df


def concat_last_context_rows(df, nRows):
    for i, row in df.iterrows():
        contextStr = ''
        contextLen = len(row['context'])
        actLen = 0
        for r in row['context']:
            if actLen >= contextLen - nRows:
                contextStr += ' ' + r
            actLen += 1
        df['context'][i] = contextStr
    return df


def split_data(df, percentage_second):
    """
        Split a dataframe in two parts.
    """
    df_1_text, df_2_text, df_1_labels, df_2_labels = train_test_split(df['source_text'].tolist(),
                                                                      df['target_text'].tolist(),
                                                                      shuffle=True,
                                                                      test_size=percentage_second,
                                                                      random_state=42,
                                                                      stratify=df['target_text'])
    df_1 = pd.DataFrame({'source_text': df_1_text, 'target_text': df_1_labels})
    df_2 = pd.DataFrame({'source_text': df_2_text, 'target_text': df_2_labels})

    return df_1, df_2


def prepare_train_datasets(train_dataset_path, num_context_tweets=2, additional_entries=True):
    """
        Split a dataframe into two equal dataframes. Augment the data if necessary.
    """

    df = pd.read_json(train_dataset_path, lines=True)

    # Augment dataset with additional entries using only context without the corresponding sarcastic response
    if additional_entries:
        sarcastic_df = df[df['label'] == 'SARCASM'].copy()
        sarcastic_df = sarcastic_df.assign(response='')
        sarcastic_df = sarcastic_df.assign(label="NOT_SARCASM")
        df = df.append(sarcastic_df)

    # Add the context-tweets to the training data
    df['source_text'] = df['context'].apply(lambda x: ' '.join(map(str, x[-num_context_tweets:])))
    df['source_text'] = df['source_text'] + df['response']
    df['target_text'] = df['label']

    # Split the dataset into two  equal sets
    train_df_1, train_df_2 = split_data(df, 0.5)

    return train_df_1, train_df_2


def prepare_test_dataset(path, num_context_tweets=2):
    """
        Prepare the test set.
    """
    df = pd.read_json(path, lines=True)

    # Add the context-tweets to the training data
    df['source_text'] = df['context'].apply(lambda x: ' '.join(map(str, x[-num_context_tweets:])))
    df['source_text'] = df['source_text'] + df['response']
    df['target_text'] = df['label']

    test_df = df.drop(labels=['context', 'response', 'id', 'label'], axis=1)

    return test_df
