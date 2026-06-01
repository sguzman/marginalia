import re

f1 = "/win/linux/Code/Text/marginalia/content/posts/american-conservatism/index.md"
f2 = "/win/linux/Code/Text/marginalia/content/posts/modern-progressive-marxism/index.md"

def process(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    
    # 1. Fix Image Indentation
    # Find any line that has leading spaces and then ![
    # and strip the leading spaces.
    new_content = re.sub(r'^[ \t]+(!\[.*?\]\(.*?\))', r'\1', content, flags=re.MULTILINE)
    
    if new_content != content:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(new_content)
        print(f"Fixed images in {filepath}")

process(f1)
process(f2)

# 2. Fix the broken tables
# I'll manually define the broken string and its replacement for modern-progressive-marxism
broken_table = """  ----------------------------------------------------------------------------------------------
  Case           Marxist or socialist  Organizational     Illustrative        Continuity
                 inheritance           bridge             policies and        rhetoric
                                                          judgment            
  -------------- --------------------- ------------------ ------------------- ------------------
  Germany SPD    Hamburg Programme     SPD describes      Workers' rights,    **Strong but
                 says SPD draws on     itself as part of  welfare state,      revised**
                 "Marxist analysis of  the labor movement reformist           
                 society"; party       and says it        democratic          
                 history page says     developed the      socialism, later    
                 Godesberg redefined   welfare state      incorporation of    
                 democratic socialism  together with      women's and new     
                 from inevitabilist    trade unions.      social movements.   
                 socialism to reform                                          
                 practice.                                                    

  United Kingdom Labour official site  Affiliated unions  NHS creation in     **Strong in
  Labour         says the party was    remain a           1948; Bank of       origin, moderated
                 formed out of the     structural part of England             in doctrine**
                 trade union movement; party life.        nationalization in  
                 historic Labour                          1946; labor-rights  
                 politics included                        link persists.      
                 common-ownership                                             
                 traditions and                                               
                 postwar                                                      
                 nationalization.                                             

  Sweden SAP and Swedish party program Dense union-party  Universalistic      **Very strong
  LO             locates the movement  cooperation        welfare state,      institutional
                 in union-political    through the labor  solidaristic wage   continuity**
                 cooperation;          wage-earner funds  setting, Meidner    
                 were proposed for                        funds to counter    
                 "economic democracy."                    concentrated        
                                                          capital ownership.  

  United States  DSA rejects           Electoral          Medicare for All,   **Strong in
  DSA, Sanders,  private-profit order  coalitions, DSA    wealth tax, Green   factions, not
  CPC            and unequal           chapters, nurses'  New Deal, right to  hegemonic in the
                 wealth-power          unions,            organize, debt-free whole
                 structures; Sanders   labor-backed issue college,            center-left**
                 and the CPC frame     campaigns.         anti-monopoly       
                 politics as workers                      language.           
                 vs corporations and                                          
                 billionaires.                                                

  Brazil PT and  PT statute defines    Labor-party nexus  Bolsa Família,      **Strong origin,
  CUT            mission as building   developed with CUT participatory       moderated
                 democratic socialism  and later mass     budgeting, labor    governing form**
                 and eliminating       social coalitions. rights,             
                 exploitation and                         anti-poverty        
                 oppression.                              institutions,       
                                                          rights-based        
                                                          developmentalism.   

  Chile Frente   Boric coalition       Coalition between  Feminism,           **Strong
  Amplio and     program says market   Broad Front        ecological          anti-neoliberal
  Apruebo        should cease          parties, Communist transition, social  continuity, plural
  Dignidad       structuring society;  Party,             rights, stronger    ideological mix**
                 coalition included    student-movement   state role, labor   
                 the Communist Party   cadres, and a      reform,             
                 and anti-neoliberal   joint policy       public-resource     
                 left currents.        observatory.       administration.     

  India CPI(M)   CPI(M) explicitly     Party-linked mass  Land reform,        **Direct Marxist
  and Kerala     seeks socialism via   organizations and  decentralization,   continuity with
  left           people's democracy    state-level left   panchayat           democratic-state
  governance     and combines          governance.        strengthening,      adaptation**
                 parliamentary and                        pro-people policy,  
                 extra-parliamentary                      strong health       
                 struggle.                                outcomes in Kerala. 
  ----------------------------------------------------------------------------------------------"""

replacement_table = """| Case | Marxist or socialist inheritance | Organizational bridge | Illustrative policies and rhetoric | Continuity judgment |
|---|---|---|---|---|
| Germany SPD | Hamburg Programme says SPD draws on "Marxist analysis of society"; party history page says Godesberg redefined democratic socialism from inevitabilist socialism to reform practice. | SPD describes itself as part of the labor movement and says it developed the welfare state together with trade unions. | Workers' rights, welfare state, reformist democratic socialism, later incorporation of women's and new social movements. | **Strong but revised** |
| United Kingdom Labour | Labour official site says the party was formed out of the trade union movement; historic Labour politics included common-ownership traditions and postwar nationalization. | Affiliated unions remain a structural part of party life. | NHS creation in 1948; Bank of England nationalization in 1946; labor-rights link persists. | **Strong in origin, moderated in doctrine** |
| Sweden SAP and LO | Swedish party program locates the movement in union-political cooperation; wage-earner funds were proposed for "economic democracy." | Dense union-party cooperation through the labor movement. | Universalistic welfare state, solidaristic wage setting, Meidner funds to counter concentrated capital ownership. | **Very strong institutional continuity** |
| United States DSA, Sanders, CPC | DSA rejects private-profit order and unequal wealth-power structures; Sanders and the CPC frame politics as workers vs corporations and billionaires. | Electoral coalitions, DSA chapters, nurses' unions, labor-backed issue campaigns. | Medicare for All, wealth tax, Green New Deal, right to organize, debt-free college, anti-monopoly language. | **Strong in factions, not hegemonic in the whole center-left** |
| Brazil PT and CUT | PT statute defines mission as building democratic socialism and eliminating exploitation and oppression. | Labor-party nexus developed with CUT and later mass social coalitions. | Bolsa Família, participatory budgeting, labor rights, anti-poverty institutions, rights-based developmentalism. | **Strong origin, moderated governing form** |
| Chile Frente Amplio and Apruebo Dignidad | Boric coalition program says market should cease structuring society; coalition included the Communist Party and anti-neoliberal left currents. | Coalition between Broad Front parties, Communist Party, student-movement cadres, and a joint policy observatory. | Feminism, ecological transition, social rights, stronger state role, labor reform, public-resource administration. | **Strong anti-neoliberal continuity, plural ideological mix** |
| India CPI(M) and Kerala left governance | CPI(M) explicitly seeks socialism via people's democracy and combines parliamentary and extra-parliamentary struggle. | Party-linked mass organizations and state-level left governance. | Land reform, decentralization, panchayat strengthening, pro-people policy, strong health outcomes in Kerala. | **Direct Marxist continuity with democratic-state adaptation** |"""

with open(f2, "r", encoding="utf-8") as f:
    content = f.read()

# Since the spacing might not match exactly due to previous modifications or line endings, we can use a regex to replace everything between the top `---------------------` and the bottom `---------------------` around the table.
# Wait, let's just find the exact boundaries.
table_start_str = "  ----------------------------------------------------------------------------------------------\n  Case           Marxist or socialist"
table_end_str = "struggle.                                outcomes in Kerala. \n  ----------------------------------------------------------------------------------------------"

if table_start_str in content and table_end_str in content:
    start_idx = content.find(table_start_str)
    end_idx = content.find(table_end_str) + len(table_end_str)
    new_content = content[:start_idx] + replacement_table + content[end_idx:]
    with open(f2, "w", encoding="utf-8") as f:
        f.write(new_content)
    print("Fixed table in modern-progressive-marxism")
else:
    print("Could not find table boundaries exactly in modern-progressive-marxism. Trying regex.")
    new_content = re.sub(r'  ----------------------------------------------------------------------------------------------\n  Case.*?  ----------------------------------------------------------------------------------------------', replacement_table, content, flags=re.DOTALL)
    if new_content != content:
        with open(f2, "w", encoding="utf-8") as f:
            f.write(new_content)
        print("Fixed table using regex.")
    else:
        print("Regex also failed to find the table.")

# What about american-conservatism? Does it have a table?
with open(f1, "r", encoding="utf-8") as f:
    c1 = f.read()
    if re.search(r'  ----------------------------------------------------------------------------------------------\n', c1):
        print("american-conservatism has a table too!")
        # Let's just strip the generic dashes if they surround an image
        new_c1 = re.sub(r'  -------------------------------------------------------------------------------------\n(!\[.*?\]\(.*?\))\n  -------------------------------------------------------------------------------------', r'\1', c1)
        if new_c1 != c1:
            with open(f1, "w", encoding="utf-8") as f:
                f.write(new_c1)
            print("Fixed image dashes in american-conservatism")
