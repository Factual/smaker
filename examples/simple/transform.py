import click
import numpy as np
import pandas as pd

@click.command()
@click.option('--input-path', required=True)
@click.option('--output-path', required=True)
@click.option('--multiplier', default=1)
@click.option('--sqrt/--no-sqrt', is_flag=True, default=False)
def main(input_path, output_path, multiplier, sqrt):
    df = pd.read_parquet(input_path)
    multiplied = df.multiply(multiplier)

    if sqrt: out_df = multiplied.pow(.5)
    else: out_df = multiplied

    out_df.to_csv(output_path, sep='\t')

if __name__=='__main__':
    main()

