# 288 QUESTIONS LOADED!

# Questions That Don't Perform Well on 100% Questions/Body Search

- "Can carnivore help with alzheimer's?"
- My mother is anorexic. What should I do?
- Can carnivore help with bone loss?
- Is carnivore diet good for kids?

# Questions That Do Perform Well on 100? Questions/Body Search

- does eating meat cause cancer?
- I've been carnivore for 6 months. why is my hba1c actually increasing since I started on carnivore?
- Why do people say we evolved to eat meat?
- is cooking meat bad? are there major carcinogens in burned meat?
- I've been on carnivore for 6 months and my psoriasis has actually gotten worse. What should i do?
- what are the best questions to ask for someone just starting out on the carnivore diet journey?

# Probably need more data to answer:

- why would people just eat meat, when every scientific study points to veganism being the healthiest diet?

# BUGS

# New Features to implement:

- Tag retrieval - Fetch several bodies based on associated matching tags.

  - First: ai will generate tags for the users question based on tags list
  - Second: retrieval will retrieve top 2(?) text bodies based on number of tags that match
    - bonus: if more than 2 with full tag matches, retrieve all and randomly provide 2 for the context to vary output

- Retrieve 5-6 questions for a query and return a random 4 for the context, so the content of the reply can have variations in the types of info returned

- If a text body to be included in context contains a certain number of characters, reduct by 1 how many can be included in total

- If context body references a person of note (from Carnivore ama topics list doc), it should programmatically pull in another body of text of info on that person

- The questions currently do not take in context from the previous parts of the conversation. Extend to take in the full context of the conversation, and create a limit to the amount of conversation context it can have

- Have responses less of a list and more natural, but still include all relevant information
