

# PoeMarketAnalyser

## Introduction

### Path of Exile (PoE)

Path of Exile is an online action role-playing game (ARPG) developed by Grinding Gear Games and released in 2013. The game belongs to the hack-and-slash type, where players explore different areas, defeat enemies, and collect equipment to improve their characters.
Unlike many other ARPGs, Path of Exile does not use a traditional gold-based economy. Instead, the game relies on a complex barter system in which various items function as currency. 

Players obtain items through gameplay activities such as defeating monsters, completing quests, or engaging in endgame content. These items can be traded between players, creating a dynamic player-driven market. Some items are very common and have almost no value, while others are extremely rare and highly desirable.

The game operates in seasonal cycles called leagues. Since the game's introduction, 41 leagues have been released. Each league introduces new mechanics, balance changes, and additional items, which can significantly affect the in-game economy. At the start of every league the economy resets, which creates a natural environment for studying how virtual markets evolve over time.

---

# Project Motivation

The player-driven economy of Path of Exile forms a complex market where thousands of items are traded and their values fluctuate over time. Because leagues periodically reset the game economy, each league represents a new economic system that evolves independently.

Analysing the dynamics of item prices during leagues provides an opportunity to study how virtual economies behave under changing conditions such as new content releases, balance changes, and player behavior.

The dataset used in this project contains daily aggregated price estimates for items across six latest leagues. Each record represents the estimated market value of a specific item on a given day.

---

# Project Objectives

The main goal of this project is to analyse the economic dynamics of Path of Exile leagues using item price data.
The analysis focuses on identifying patterns in item price evolution and measuring economic indicators that describe the state of the in-game market.

The specific objectives are:

1. Analyse the distribution and temporal dynamics of item prices.
2. Measure market stability by analysing price volatility.
3. Construct a **currency purchasing power index** based on a basket of representative items.
4. Compare different leagues using aggregated economic indicators.
5. Identify similarities between leagues using clustering techniques.

---

# Dataset Description

The dataset used in this project consists of two main components:

1. Items dataset
2. Currency dataset

These datasets provide information about the value of items and exchange rates between currencies in the game economy.

# Items Dataset

The item dataset contains daily estimated prices for items in each league.
Each record represents the estimated market value of an item for a given day.

| Column     | Description                                 |
| ---------- | ------------------------------------------- |
| League     | Name of the league                          |
| Date       | Date of the price estimate                  |
| Type       | Item category (e.g. UniqueWeapon, BaseType) |
| Name       | Name of the item                            |
| BaseType   | Base type of the item                       |
| Variant    | Variant of the item if applicable           |
| Links      | Number of links in the item if applicable   |
| Value      | Estimated market value of the item          |
| Confidence | Reliability of the price estimate           |


The **Confidence** column indicates the reliability of the estimated price.

| Confidence | Meaning                                                            |
| ---------- | ------------------------------------------------------------------ |
| High       | The value is based on many observations and is considered reliable |
| Medium     | The estimate is based on a moderate number of observations         |
| Low        | The value is based on very few observations and may be inaccurate  |

Low confidence values may occur when items are very rare and only a few listings are available in the market.

---

# Currency Dataset

The currency dataset describes exchange rates between different in-game currencies.

Unlike traditional economies, Path of Exile uses multiple items as currencies. These items can be exchanged with each other, forming a complex currency market. Each record represents the exchange rate between two currencies at a specific time.

| Column     | Description                                |
| ---------- | ------------------------------------------ |
| Date       | Date of the exchange rate                  |
| Get        | Currency received in the trade             |
| Pay        | Currency paid in the trade                 |
| Value      | Exchange rate between the currencies       |
| Confidence | Reliability of the estimated exchange rate |

---

# Data Characteristics

The dataset exhibits several important characteristics:

1. Item prices are strongly right-skewed because most items are inexpensive while a small number of rare items are extremely valuable.
2. Prices are recorded daily, which allows analysis of how item values evolve during a league.
3. Each league represents a separate economic environment with its own supply and demand dynamics.

---

# Expected Outcomes

The project aims to provide insights into the structure and evolution of the Path of Exile in-game economy.

The results will help identify:

* how item prices evolve during a league
* how stable the market is
* how the purchasing power of currency changes over time
* whether leagues exhibit similar economic structures


