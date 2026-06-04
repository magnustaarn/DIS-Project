DROP TABLE IF EXISTS public.links_to;
DROP TABLE IF EXISTS runs;
DROP TABLE IF EXISTS pages;

CREATE TABLE pages (
    page_id SERIAL PRIMARY KEY,
    title VARCHAR(255) UNIQUE NOT NULL,
    is_scraped BOOLEAN DEFAULT FALSE
);

CREATE TABLE runs (
    run_id SERIAL PRIMARY KEY,
    username VARCHAR(50),
    start_page_id INT NOT NULL,
    end_page_id INT NOT NULL,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    total_clicks INT DEFAULT 0,
    CONSTRAINT fk_start_page FOREIGN KEY (start_page_id) REFERENCES pages(page_id),
    CONSTRAINT fk_end_page FOREIGN KEY (end_page_id) REFERENCES pages(page_id)
);

CREATE TABLE public.links_to (
    source_page_id INT NOT NULL,
    target_page_id INT NOT NULL,
    PRIMARY KEY (source_page_id, target_page_id),
    CONSTRAINT fk_source FOREIGN KEY (source_page_id) REFERENCES pages(page_id) ON DELETE CASCADE,
    CONSTRAINT fk_target FOREIGN KEY (target_page_id) REFERENCES pages(page_id) ON DELETE CASCADE
);
