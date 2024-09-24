import pandas as pd        

def move_column_to_pos(df, column_name, pos):
    
    columns = list(df.columns)
    if column_name in columns:
        columns.remove(column_name)
    columns.insert(pos, column_name)
    return df[columns]
def move_rows_with_value_to_end(df, column_name, value):
    df_without_value = df[df[column_name] != value]
    df_with_value = df[df[column_name] == value]
    df_reordered = pd.concat([df_without_value, df_with_value], ignore_index=True)
    
    return df_reordered

