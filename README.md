
# First Aid Kit telegram bot

This a telegram bot, that will help you to manage the content of your first aid kit.

Bot simply provides control over content of table from sqlite database. Each chat has control over its own first aid kits.

The content of first aid kit could be described as csv file. Check file [input_example.csv](aid/tests/input_example.csv) as example of input.

Also, medicine could be added one by one.
 

## Installation

Install requirements for project

```bash
  pip install -r requirements.txt
```


## Usage

To launch bot run following command
```bash
python3 bot.py
```


## Running Tests

To run tests, run the following command

```bash
  python3 aid/aid_test.py
```


## Full list of bot commands

| Command            | Description                                 |
|:-------------------|:--------------------------------------------|
| /start             | Start bot and connect to your first aid kit |
| /delete_aid_kit    | Delete first aid kit and all it's content   |
| /search            | Search medicine in first aid kit            |
| /take_med          | Take medicine from first aid kit            |
| /add_med           | Add medicine to first aid kit               |
| /list_med          | List all medicines                          |
| /list_med_category | List all categories of medicines            |
| /import_csv        | Import medicines from csv file              |
| /export_csv        | Export current first aid kit to csv file    |
| /cancel            | Cancel current command                      |

    