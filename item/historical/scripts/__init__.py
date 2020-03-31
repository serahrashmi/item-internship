from functools import lru_cache

import pandas as pd
import pycountry

from item.common import paths
from item.historical import source_str
from . import T001
from .util.managers.dataframe import ColumnName, DataframeManager


MODULES = {
    1: T001
}


# Non-ISO names appearing in 1 or more data sets
COUNTRY_NAME = {
    "Montenegro, Republic of": "Montenegro",
    "Bosnia-Herzegovina": "Bosnia and Herzegovina",
    "Korea": "Korea, Republic of",
    "Serbia, Republic of": "Serbia",
}


def process(id):
    """Process a data set given its *id*."""
    # Creating the dataframe and viewing the data

    # Creating a dataframe from the csv data
    id_str = source_str(id)
    path = paths['data'] / 'historical' / 'input' / f'{id_str}_input.csv'
    df = pd.read_csv(path)

    # Get the module for this data set
    dataset_module = MODULES[1]

    try:
        # Remove unnecessary columns
        df.drop(columns=dataset_module.DROP_COLUMNS, inplace=True)
        print('Drop {len(dataset_module.DROP_COLUMNS)} extra column(s)')
    except AttributeError:
        # No variable DROP_COLUMNS in dataset_module
        print(f'No columns to drop for {id_str}')

    # Call the dataset-specific processing
    df = dataset_module.process(df)
    print(f'{len(df)} observations')

    # Perform common cleaning tasks

    # Assign ISO-3166 alpha-3 codes to *df* using a country name column
    column = 'Country'  # TODO read this name from dataset_module
    # Use pandas.Series.apply() to apply the same function to each entry in
    # the given column
    # TODO speed up further using df[column].unique() and then Series.replace
    df[ColumnName.ISO_CODE.value] = df[column].apply(alpha_3_for_name)

    # TODO Assign iTEM regions based on ISO codes

    # Reordering the columns
    #
    # Rule: The columns should follow the order established in the latest
    # template
    dfm = DataframeManager(source_str(id))
    df = dfm.reorder_columns(df)

    # Exporting results

    # Programming Friendly View
    dfm.create_programming_friendly_file(df)

    # User Friendly View
    dfm.create_user_friendly_file(df)

    # Return the data for use by other code
    return df


@lru_cache()
def alpha_3_for_name(name):
    """Return the ISO-3166 alpha-3 code for a country *name*."""
    # lru_cache() ensures this function call is as fast as a dictionary lookup
    # after the first time each country name is seen

    # Maybe map a known, non-standard value to a standard value
    name = COUNTRY_NAME.get(name, name)

    # Use pycountry's built-in, case-insensitive lookup on all fields including
    # name, official_name, and common_name
    return pycountry.countries.lookup(name).alpha_3
