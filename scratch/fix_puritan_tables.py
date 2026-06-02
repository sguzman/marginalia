import re

f = "/win/linux/Code/Text/marginalia/content/posts/puritan-moral-psychology/index.md"
with open(f, "r", encoding="utf-8") as file:
    content = file.read()

# Replace Table 1
table1_regex = r"  -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------\n  Puritan structure Early expression    Later progressive or Evidence.*?  -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------"

replacement1 = """| Puritan structure | Early expression | Later progressive or liberal analogue | Evidence |
|---|---|---|---|
| Covenantal community | Collective covenant with God and public duty in Winthrop | "Contract with the people," social citizenship, rights plus obligation | [\\[14\\]](https://history.hanover.edu/courses/excerpts/212winth.html) |
| Moralized authority | Liberty exists through subjection to "good, just, and honest" rule | Expert administration justified as protecting welfare, equality, or inclusion | [\\[15\\]](https://teachingamericanhistory.org/document/on-liberty/) |
| Public discipline | Church/civil censure in Keayne case; scriptural law in colony codes | Inspection, compliance offices, bias reporting, regulatory enforcement | [\\[16\\]](https://teachingamericanhistory.org/document/admonishment-and-reconciliation-of-robert-keayne-with-the-church-1639-1640/) |
| Declension and jeremiad | Fear of covenant-breaking and collective shame | Reform rhetoric centered on national sin, hypocrisy, or failure to live ideals | [\\[17\\]](https://history.hanover.edu/courses/excerpts/212winth.html) |
| Confession and self-scrutiny | Humiliation before God, Edwardsian self-examination | Testimony, awareness-raising, apology, public acknowledgment of harm or bias | [\\[18\\]](https://history.hanover.edu/courses/excerpts/212winth.html) |
| Exemplary mission | "City upon a hill," providential errand | Manifest Destiny, democratic crusade, human-rights diplomacy | [\\[19\\]](https://nationalhumanitiescenter.org/tserve/nineteen/nkeyinfo/mandestiny.htm) |
| Purification | Restraint of corruption, vice, false worship | Campaigns against drink, labor exploitation, segregation, discriminatory institutions, and later exclusionary climates | [\\[20\\]](https://teachingamericanhistory.org/document/the-body-of-liberties-of-the-massachusetts-colony-in-new-england/) |"""

content = re.sub(table1_regex, replacement1, content, flags=re.DOTALL)

# Replace Table 2
table2_regex = r"  --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------\n  Date           Node                 Key actors      Genealogical          Sources.*?  --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------"

replacement2 = """| Date | Node | Key actors | Genealogical significance | Sources |
|---|---|---|---|---|
| 1630 | Covenant commonwealth | John Winthrop | Community defined by covenant, mutual obligation, and exemplary mission | [\\[27\\]](https://history.hanover.edu/courses/excerpts/212winth.html) |
| 1641--1647 | Scriptural civil order | Massachusetts General Court | Civil liberty and law explicitly anchored to divine rule and public discipline | [\\[28\\]](https://teachingamericanhistory.org/document/the-body-of-liberties-of-the-massachusetts-colony-in-new-england/) |
| 1639--1645 | Public admonition and "moral" liberty | Robert Keayne, Winthrop | Economic conduct and liberty moralized and publicly supervised | [\\[29\\]](https://teachingamericanhistory.org/document/admonishment-and-reconciliation-of-robert-keayne-with-the-church-1639-1640/) |
| 1730s--1740s | Revival and introspection | Jonathan Edwards | Intensified self-scrutiny, awakening, and conversion-centered public religion | [\\[30\\]](https://www.ccel.org/e/edwards/sermons.html) |
| 1820s--1840s | Activist evangelical reform | Charles Finney and revival networks | Reform through organized means; moral action applied to society | [\\[31\\]](https://nationalhumanitiescenter.org/tserve/nineteen/nkeyinfo/nevanrev.htm) |
| 1830s--1850s | Moral suasion | Garrison, AASS, Grimké | Slavery attacked as collective sin through testimony, persuasion, and shame | [\\[32\\]](https://teachingamericanhistory.org/document/to-the-public/) |
| 1870s--1920s | Social Gospel | Rauschenbusch | Social salvation; politics and administration as moral instruments | [\\[33\\]](https://www.britannica.com/event/Social-Gospel) |
| 1889 onward | Settlement movement | Addams, Starr, Kelley | Moral reform embodied in neighborhood institutions and regulation | [\\[34\\]](https://www.loc.gov/exhibitions/join-in-voluntary-associations-in-america/about-this-exhibition/a-nation-of-joiners/changing-america/settlement-houses-hull-house/) |
| 1909--1912 | Progressive statism | Croly, Theodore Roosevelt, Progressive Party | National administrative capacity justified by welfare and justice | [\\[35\\]](https://teachingamericanhistory.org/document/the-promise-of-american-life/) |
| 1935--1944 | Welfare-state rights | FDR, Social Security Board | Economic security reframed as a right and administered by national institutions | [\\[36\\]](https://www.ssa.gov/history/35act.html) |
| 1947--1965 | Rights-state expansion | Truman committee, Brown, LBJ | Moral equality juridified and bureaucratized | [\\[37\\]](https://teachingamericanhistory.org/document/to-secure-these-rights-the-report-of-the-presidents-committee-on-civil-rights/) |
| 1965 onward | Affirmative-action governance | LBJ, EEOC, OFCCP | Nondiscrimination plus proactive remediation enforced through federal oversight | [\\[38\\]](https://www.archives.gov/federal-register/codification/executive-order/11246.html) |
| 2000s--2020s | DEI, bias response, call-out culture | Universities, HR systems, PEN America's critics and defenders | Harm-centered moral language, institutional monitoring, and contested discipline of speech/status | [\\[39\\]](https://www.smith.edu/your-campus/offices-services/equity-inclusion/policies-resources/bias-response-team) |"""

content = re.sub(table2_regex, replacement2, content, flags=re.DOTALL)

# Strip dashes around the image
content = re.sub(r'  ----------------------------------------------------------------------------------------\n(!\[.*?\]\(.*?\))\n\n  ----------------------------------------------------------------------------------------', r'\1\n', content)

with open(f, "w", encoding="utf-8") as file:
    file.write(content)

print("Fixed tables and image in puritan-moral-psychology.")
