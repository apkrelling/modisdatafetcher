```mermaid
flowchart TD
A[[get_opendap_urls]] ==> B[[get_subsetted_dataset]]
I([check_settings]) -.-> A
J([check_date_format]) -.-> I
K([get_filelist_command]) -.-> A
G -.-> A

C([get_dataset_keys]) -.-> B
B ==> D[[plots]]
D ==> E[[save_dataset]]
C -.-> E
G([get_dates]) -.-> E
H([find_nearest]) -.-> E

```
[comment]: <> (https://mermaid.js.org/syntax/flowchart.html)