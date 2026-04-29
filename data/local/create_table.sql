CREATE TABLE users (
    user_id INT PRIMARY KEY,
    signup_date DATE,
    region TEXT
);

CREATE TABLE athletes (
    athlete_id INT PRIMARY KEY,
    name TEXT,
    sport TEXT,
    team TEXT
);

CREATE TABLE tokens (
    token_id INT PRIMARY KEY,
    athlete_id INT,
    initial_price NUMERIC
);

CREATE TABLE trades (
    trade_id INT PRIMARY KEY,
    user_id INT,
    token_id INT,
    trade_date DATE,
    quantity INT,
    price NUMERIC
);

CREATE TABLE events (
    athlete_id INT,
    event_date DATE,
    performance_score NUMERIC
);