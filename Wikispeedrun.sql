CREATE TABLE users (
	user_id SERIAL PRIMARY KEY,
	username VARCHAR(50) UNIQUE NOT NULL,
	email VARCHAR(100) UNIQUE NOT NULL,
	password_hash VARCHAR(255) NOT NULL
);

CREATE TABLE pages (
	page_id SERIAL PRIMARY KEY,
	title VARCHAR(255) UNIQUE NOT NULL
);

CREATE TABLE runs (
	run_id SERIAL PRIMARY KEY,
	user_id INT NOT NULL,
	start_page_id INT NOT NULL,
	end_page_id INT NOT NULL,
	start_time TIMESTAMP NOT NULL,
	end_time TIMESTAMP,
	total_clicks INT DEFAULT 0,
	CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
	CONSTRAINT fk_start_page FOREIGN KEY (start_page_id) REFERENCES pages(page_id),
	CONSTRAINT fk_end_page FOREIGN KEY (end_page_id) REFERENCES pages(page_id)
);

CREATE TABLE runs (
	source_page_id INT NOT NULL,
	target_page_id INT NOT NULL,
	PRIMARY KEY (source_page_id, target_page_id),
	CONSTRAINT fk_source FOREIGN KEY (source_page_id) REFERENCES pages(page_id) ON DELETE CASCADE,
	CONSTRAINT fk_target FOREIGN KEY (target_page_id) REFERENCES pages(page_id) ON DELETE CASCADE
)