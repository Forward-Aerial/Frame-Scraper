import pandas as pd

pd.set_option("max_rows", None)
df = pd.read_csv("records.csv")
print(pd.concat([df["p1_character"], df["p2_character"]]).value_counts())
