
def query_dataset(dataset):
    if dataset.groups:
        for grp in dataset.groups:
            print(grp)
            text = "    "
            for var in dataset.groups[grp].variables:
                text += f"{var},"
            print(text.rstrip(","))
    else:
        text = ""
        for var in dataset.variables:
            text += f"{var},"
        print(text.rstrip(","))
