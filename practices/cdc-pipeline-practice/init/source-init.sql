CREATE TABLE IF NOT EXISTS mytable (
  id SERIAL PRIMARY KEY,
  name VARCHAR(100),
  age INT
);

INSERT INTO mytable (name, age) VALUES ('Alice', 28), ('Bob', 35);

-- CDC를 위한 publication 생성
CREATE PUBLICATION mypub FOR TABLE mytable;
