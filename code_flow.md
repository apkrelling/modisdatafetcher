```mermaid
flowchart LR
A[[get_opendap_urls]]
I([check_date_format]) -.-> A
L([check_space_res]) -.-> A
M([check_time_res]) -.-> A
N([check_coords]) -.-> A
K([get_filelist_command]) -.-> A
G([get_dates]) -.-> A

```

```mermaid
flowchart TD
B[[get_subsetted_dataset]]
C([get_dataset_keys]) -.-> B
```

```mermaid
flowchart TD
E[[save_dataset]]
C([get_dataset_keys]) -.-> E
G([get_dates]) -.-> E
```

[comment]: <> (https://mermaid.js.org/syntax/flowchart.html)