from datetime import datetime, timezone

from psycopg2.extras import execute_values
from flask import Blueprint, render_template, request, redirect, url_for, session

from db import get_db
from scraper import get_wiki_links

game_bp = Blueprint("game", __name__)


@game_bp.route("/")
def index():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT r.username, p1.title, p2.title,
               r.total_clicks,
               EXTRACT(EPOCH FROM (r.end_time - r.start_time))::int AS seconds
        FROM runs r
        JOIN pages p1 ON p1.page_id = r.start_page_id
        JOIN pages p2 ON p2.page_id = r.end_page_id
        WHERE r.end_time IS NOT NULL AND r.username IS NOT NULL
        ORDER BY r.total_clicks ASC, seconds ASC
        LIMIT 10;
    """)
    leaderboard = cur.fetchall()
    cur.execute("SELECT COUNT(*) FROM pages;")
    page_count = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM runs WHERE end_time IS NOT NULL;")
    run_count = cur.fetchone()[0]
    cur.close()
    conn.close()
    return render_template("index.html", leaderboard=leaderboard,
                           page_count=page_count, run_count=run_count)


@game_bp.route("/play", methods=["GET", "POST"])
def play_setup():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT title FROM pages ORDER BY RANDOM() LIMIT 50;")
    pages = [r[0] for r in cur.fetchall()]
    cur.close()
    conn.close()

    if request.method == "POST":
        start_title = request.form["start_page"].strip().replace(" ", "_")
        end_title = request.form["end_page"].strip().replace(" ", "_")

        conn = get_db()
        cur = conn.cursor()
        for title in [start_title, end_title]:
            cur.execute(
                "INSERT INTO pages (title) VALUES (%s) ON CONFLICT (title) DO NOTHING;",
                (title,),
            )
        conn.commit()

        cur.execute("SELECT page_id FROM pages WHERE title = %s;", (start_title,))
        start_id = cur.fetchone()[0]
        cur.execute("SELECT page_id FROM pages WHERE title = %s;", (end_title,))
        end_id = cur.fetchone()[0]

        cur.execute(
            """INSERT INTO runs (start_page_id, end_page_id, start_time)
               VALUES (%s, %s, %s) RETURNING run_id;""",
            (start_id, end_id, datetime.now(timezone.utc)),
        )
        run_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()

        session["run_id"] = run_id
        session["end_title"] = end_title
        session["clicks"] = 0
        return redirect(url_for("game.play_page", title=start_title))

    return render_template("play_setup.html", pages=pages)


@game_bp.route("/play/<path:title>")
def play_page(title):
    if "run_id" not in session:
        return redirect(url_for("game.play_setup"))

    end_title = session.get("end_title", "")
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT page_id, is_scraped FROM pages WHERE title = %s;", (title,))
    row = cur.fetchone()

    if not row:
        cur.execute(
            "INSERT INTO pages (title) VALUES (%s) ON CONFLICT (title) DO NOTHING RETURNING page_id;",
            (title,),
        )
        result = cur.fetchone()
        if result:
            page_id = result[0]
        else:
            cur.execute("SELECT page_id FROM pages WHERE title = %s;", (title,))
            page_id = cur.fetchone()[0]
        is_scraped = False
        conn.commit()
    else:
        page_id, is_scraped = row

    if is_scraped:
        cur.execute("""
            SELECT p.title FROM links_to lt
            JOIN pages p ON p.page_id = lt.target_page_id
            WHERE lt.source_page_id = %s
            ORDER BY p.title;
        """, (page_id,))
        links = [r[0] for r in cur.fetchall()]
        cur.close()
        conn.close()
    else:
        cur.close()
        conn.close()
        raw_links = get_wiki_links(title)
        conn = get_db()
        cur = conn.cursor()
        for link in raw_links:
            cur.execute(
                "INSERT INTO pages (title) VALUES (%s) ON CONFLICT (title) DO NOTHING;",
                (link,),
            )
        conn.commit()
        cur.execute("SELECT title, page_id FROM pages WHERE title = ANY(%s);", (raw_links,))
        title_to_id = dict(cur.fetchall())
        link_pairs = [(page_id, title_to_id[l]) for l in raw_links if l in title_to_id]
        if link_pairs:
            execute_values(
                cur,
                "INSERT INTO links_to (source_page_id, target_page_id) VALUES %s ON CONFLICT DO NOTHING;",
                link_pairs,
            )
        cur.execute("UPDATE pages SET is_scraped = TRUE WHERE page_id = %s;", (page_id,))
        conn.commit()
        cur.close()
        conn.close()
        links = raw_links

    won = (title == end_title)
    return render_template("play_page.html",
                           title=title,
                           links=links,
                           end_title=end_title,
                           clicks=session.get("clicks", 0),
                           won=won,
                           run_id=session.get("run_id"))


@game_bp.route("/click/<path:title>")
def click_link(title):
    if "run_id" not in session:
        return redirect(url_for("game.play_setup"))

    session["clicks"] = session.get("clicks", 0) + 1

    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "UPDATE runs SET total_clicks = %s WHERE run_id = %s;",
        (session["clicks"], session["run_id"]),
    )
    conn.commit()
    cur.close()
    conn.close()

    return redirect(url_for("game.play_page", title=title))


@game_bp.route("/finish", methods=["GET", "POST"])
def finish_run():
    run_id = session.get("run_id")
    if not run_id:
        return redirect(url_for("game.index"))

    # POST: username submitted, save and finalize the run
    if request.method == "POST":
        username = request.form["username"].strip() or "Anonymous"

        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            """UPDATE runs SET end_time = %s, username = %s
               WHERE run_id = %s
               RETURNING total_clicks, start_page_id, end_page_id;""",
            (datetime.now(timezone.utc), username, run_id),
        )
        row = cur.fetchone()
        conn.commit()

        total_clicks = row[0] if row else 0
        cur.execute("SELECT title FROM pages WHERE page_id = %s;", (row[1],))
        start_title = cur.fetchone()[0]
        cur.execute("SELECT title FROM pages WHERE page_id = %s;", (row[2],))
        end_title = cur.fetchone()[0]
        cur.close()
        conn.close()

        clicks = session.pop("clicks", total_clicks)
        session.pop("run_id", None)
        session.pop("end_title", None)

        return render_template("finish.html",
                               saved=True,
                               username=username,
                               clicks=clicks,
                               start_title=start_title,
                               end_title=end_title)

    # GET: show the username form, passing along click count from session
    return render_template("finish.html",
                           saved=False,
                           clicks=session.get("clicks", 0),
                           start_title=None,
                           end_title=session.get("end_title", ""))


@game_bp.route("/leaderboard")
def leaderboard():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT r.username, p1.title, p2.title,
               r.total_clicks,
               EXTRACT(EPOCH FROM (r.end_time - r.start_time))::int AS seconds,
               r.start_time::date
        FROM runs r
        JOIN pages p1 ON p1.page_id = r.start_page_id
        JOIN pages p2 ON p2.page_id = r.end_page_id
        WHERE r.end_time IS NOT NULL AND r.username IS NOT NULL
        ORDER BY r.total_clicks ASC, seconds ASC
        LIMIT 50;
    """)
    runs = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("leaderboard.html", runs=runs)
