import re

f2 = "/win/linux/Code/Text/marginalia/content/posts/modern-progressive-marxism/index.md"

broken_table_2 = """  -----------------------------------------------------------------------
  Country               Union density          Adjusted What the numbers
                                             bargaining suggest
                                               coverage 
  ----------------- ----------------- ----------------- -----------------
  Sweden                        65.9%               88% Progressive
                                                        politics rests on
                                                        dense
                                                        labor-market
                                                        institutions and
                                                        sectoral
                                                        bargaining.

  United Kingdom                  22%             40.2% The labor link
                                                        remains
                                                        significant but
                                                        far weaker than
                                                        in classic Nordic
                                                        social democracy.

  Germany                       14.1%               49% Union membership
                                                        is lower, but
                                                        bargaining
                                                        institutions
                                                        still preserve a
                                                        labor-social
                                                        compromise.

  United States                  9.9%             11.1% Progressive
                                                        politics exists,
                                                        but class
                                                        organization is
                                                        much thinner and
                                                        more
                                                        factionalized.
  -----------------------------------------------------------------------"""

replacement_table_2 = """| Country | Union density | Adjusted bargaining coverage | What the numbers suggest |
|---|---|---|---|
| Sweden | 65.9% | 88% | Progressive politics rests on dense labor-market institutions and sectoral bargaining. |
| United Kingdom | 22% | 40.2% | The labor link remains significant but far weaker than in classic Nordic social democracy. |
| Germany | 14.1% | 49% | Union membership is lower, but bargaining institutions still preserve a labor-social compromise. |
| United States | 9.9% | 11.1% | Progressive politics exists, but class organization is much thinner and more factionalized. |"""

with open(f2, "r", encoding="utf-8") as f:
    content = f.read()

table_start_str = "  -----------------------------------------------------------------------\n  Country               Union density          Adjusted What the numbers"
table_end_str = "                                                        factionalized.\n  -----------------------------------------------------------------------"

if table_start_str in content and table_end_str in content:
    start_idx = content.find(table_start_str)
    end_idx = content.find(table_end_str) + len(table_end_str)
    new_content = content[:start_idx] + replacement_table_2 + content[end_idx:]
    with open(f2, "w", encoding="utf-8") as f:
        f.write(new_content)
    print("Fixed second table in modern-progressive-marxism")
else:
    print("Could not find table boundaries exactly.")
    new_content = re.sub(r'  -----------------------------------------------------------------------\n  Country.*?  -----------------------------------------------------------------------', replacement_table_2, content, flags=re.DOTALL)
    if new_content != content:
        with open(f2, "w", encoding="utf-8") as f:
            f.write(new_content)
        print("Fixed second table using regex.")
    else:
        print("Regex also failed to find the table.")

# What about american-conservatism? Does it have any OTHER tables?
f1 = "/win/linux/Code/Text/marginalia/content/posts/american-conservatism/index.md"
with open(f1, "r", encoding="utf-8") as f:
    c1 = f.read()
    if re.search(r'  -----------------------------------------------------------------------\n', c1):
        print("american-conservatism has a table too!")
