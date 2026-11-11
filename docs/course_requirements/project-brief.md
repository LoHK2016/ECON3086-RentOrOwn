# ECON3086 Group Project Brief

Source: `ECON3086-6c-Project_Brief.pdf` (Henry Tang, ECON3086 · Python Programming for FinTech). This is a faithful markdown transcription of the 13 slides. The group project is **40% of the course**.

## The project

- Groups of about 5. Your group is the final list on Moodle.
- Any **FinTech** topic of your own choice.
- Python does the work.
- An **8-minute live presentation** at the last class.
- Hand in your **code and your slides** on Moodle.

## What a perfect project looks like

**1 · An application**
- It solves a real money problem.
- It gets live data itself, every day if it can.
- Someone could actually use it.

**2 · It shows it is right**
- If it decides (buy, which bank, which fund), check the answer.
- Check against past data, or by hand.
- Say what it cannot tell you.

Example: a program that reads today's FX rates and fees from five banks every morning and tells you the cheapest way to send money abroad, **and** a check, by hand, that its answer is right.

> You do not need a data analysis or a model. Use one if your application needs it to decide. **The perfect project is an application people would use, and it is right.**

## Topics from past semesters

These are **not** the best projects, just different topics. Each can be done well or not well. What you do with the topic is what counts.

- **Investing**: technical analysis (moving averages, candlesticks), fundamental analysis, portfolio optimisation, algo trading and back-testing, option mispricing detection.
- **Hong Kong money**: MPF fund selection, MPF plan performance and comparison, HK IPO investment prediction, the cheapest way to send money abroad, shop rent forecast.
- **News and opinions**: sentiment of social media posts, news sentiment, social-media replies and the stock market, US elections and energy stocks.
- **Apps and AI**: robo-adviser, price alerts on Telegram and Discord, broker portfolio manager, personal finance from a bank statement, a finance chatbot.

### Past projects (examples)

Investing:
- **Betting-against-beta screener**: re-built a published finance paper on real data, then screened stocks live.
- **ESG portfolio with news sentiment**: scored news with a finance language model and built a portfolio from it.
- **Trading system**: technical indicators, machine-learning signals, a risk check and alerts.
- **Portfolio optimiser**: forum mood, technical indicators and a risk questionnaire, with an Excel report.
- **Portfolio return forecast**: added geopolitical-risk and US economic data, and emailed a PDF report.
- **Industry stock screener**: valued S&P 500 stocks by industry, with Telegram alerts and LLM summaries.

Hong Kong money:
- **Cheapest way to send money abroad**: scraped FX rates and fees from five Hong Kong banks and Wise, and picked the cheapest.
- **Shop rent forecast**: scraped Hong Kong shop listings, forecast the rent, and showed it on a map.
- **Personal finance manager**: read a PDF bank statement and suggested how much to save.
- **HK and US price alerts**: watched prices live and sent an alert when a stock moved past a level.
- **MPF plan comparison**: tracked and compared how MPF plans performed.

News and opinions:
- **News sentiment bot**: scored the news with a language model and sent the result to Telegram.
- **Social-media replies and the market**: the mood of replies to a politician's posts, set against the S&P 500.
- **US elections and energy stocks**: did energy stocks move unusually around five US elections?
- **Trading rules with headline sentiment**: moving averages, a model and the news mood, with Telegram alerts.
- **AI social-media dashboard**: turned live financial news into posts written by an LLM, and published them.

Apps and AI:
- **AI robo-adviser**: asks about your goals, picks funds with an LLM, and back-tests the portfolio.
- **Stock alert platform**: prices, news and buy/hold/sell signals, with alerts on Discord and Telegram.
- **Stock helper app**: a desktop app with charts, ratios, a price forecast and news sentiment.
- **Broker portfolio manager**: read holdings from Futu and Interactive Brokers and measured the risk.
- **Stock rating system**: rated stocks from their financial statements and live prices.
- **A "finance professor" chatbot**: an LLM that answers investment questions.

## Project evaluation

| Weight | Criterion |
| --- | --- |
| 20% | Practical application |
| 30% | Basic programming |
| 40% | Library usage |
| 10% | Presentation |

One mark for the group, then adjusted for each person (see "Your own mark").

### Practical application (20%)

- Pick a FinTech topic of your choice.
- Define a problem, and solve it.
- Build a FinTech application. Data analysis or a model is welcome when the application uses it.
- Avoid Kaggle problems and Kaggle datasets.

### Basic programming (30%)

> **Only Python code earns these marks.** Other code is fine (a web page in HTML or JavaScript, SQL, a no-code tool) but it earns no coding marks. **A project with no Python at all scores 0.**

Marked on:
- Correct use of what has been taught:
  - Variables, numbers, text, f-strings (week 2)
  - Functions, tested with `assert` (week 2)
  - Conditions: `if` / `elif` / `else`, `and` / `or` / `not` (week 3)
  - Lists (week 3)
  - `for` loops (week 4)
  - Dictionaries (week 4)
  - Loop patterns: best so far, first time (week 5)
  - What is taught in the coming weeks, or anything else used correctly
- Correct logic
- Simple logic
- Code that is easy to read

### Library usage (40%)

Correct use of libraries, for example:
- Getting data online: a library, an API, or web scraping
- Working with other systems: Google Sheets, Telegram, an LLM
- Charts and data visualisation
- Statistical or machine-learning models, and prediction
- Anything else learnt in class, or somewhere else

> The harder the library, used **correctly**, the higher the mark.

### Presentation (10%)

8 minutes, live, at the last class. Cover:
- The problem you are solving
- How your program solves it
- A demo of the program
- The interesting libraries you used
- Any clever logic you want to show off

Marked on a good flow, clear points and a good pace. You do not have to show code; show it if it helps you explain.

## Using AI

- You may use AI to help you write code.
- But code that runs and looks professional can still be **wrong**.
- **Understand every line you hand in**, and check the results are right.
- The lecturer may ask any of you about any part of your code. If you cannot explain it, it earns no marks.

## Your own mark

- Everyone in the group starts with the same mark, from the evaluation above.
- It is then adjusted using your self-evaluation and your teammates' peer evaluation (a form after the presentation).
- Everyone is expected to write code. This is a programming course.

> **If you did not write any code for your group project, you get no score for the project.**
