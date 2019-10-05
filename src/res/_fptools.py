import pandas as pd


def grid_average(grid_groups, output_dir: str):
    for grid_group in grid_groups:
        average_grid = pd.DataFrame()
        i = 0
        for grid_file in grid_groups[grid_group]:
            if i == 0:
                average_grid = pd.read_csv(grid_file, skiprows=list(range(4)), sep='\s+', header=None, index_col=False)
            else:
                average_grid += pd.read_csv(grid_file, skiprows=list(range(4)), sep='\s+', header=None,
                                            index_col=False)
            i += 1
        average_grid /= i
        os.makedirs(output_dir, exist_ok=True)
        out_path = output_dir + '\\' + grid_group + '.grd'
        average_grid.to_csv(out_path, sep=' ', header=False, index=False)
        with open(out_path, 'r+') as f:
            content = f.read()
            f.seek(0, 0)
            f.write('DSAA\n150 150\n0 0.7500001\n0 0.7500001\n0 1.000000\n' + content)
