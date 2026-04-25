"""Database query helpers for the P0 Counsly API."""

from typing import Any

from psycopg import AsyncConnection
from psycopg.rows import dict_row

from app.config import settings


def _scalar_config(value: Any) -> Any:
    return value


async def fetch_config(conn: AsyncConnection) -> dict[str, Any]:
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute("SELECT config_key, value_json FROM app_config")
        rows = await cur.fetchall()
    return {str(row["config_key"]): _scalar_config(row["value_json"]) for row in rows}


async def fetch_data_freshness(conn: AsyncConnection) -> dict[str, str]:
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute("SELECT dataset_name, freshness_status FROM data_freshness")
        rows = await cur.fetchall()
    return {str(row["dataset_name"]): str(row["freshness_status"]) for row in rows}


async def dataset_is_verified(conn: AsyncConnection, dataset_name: str) -> bool:
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            "SELECT freshness_status FROM data_freshness WHERE dataset_name = %s",
            (dataset_name,),
        )
        row = await cur.fetchone()
    return bool(row and row["freshness_status"] == "verified")


async def get_session_context(conn: AsyncConnection, app_user_id: str) -> dict[str, Any] | None:
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            SELECT
                au.id AS app_user_id,
                ai.email,
                ai.display_name,
                w.id AS workspace_id,
                EXISTS (
                    SELECT 1
                    FROM subscriptions s
                    WHERE s.workspace_id = w.id
                      AND s.status = %s
                      AND (s.ends_at IS NULL OR s.ends_at > now())
                ) AS paid
            FROM app_users au
            JOIN auth_identities ai ON ai.id = au.auth_identity_id
            JOIN workspaces w ON w.app_user_id = au.id
            WHERE au.id = %s AND au.status = %s
            """,
            ("active", app_user_id, "active"),
        )
        return await cur.fetchone()


async def get_workspace_id(conn: AsyncConnection, app_user_id: str) -> str:
    context = await get_session_context(conn, app_user_id)
    if not context:
        raise LookupError("workspace not found")
    return str(context["workspace_id"])


async def get_student_profile(conn: AsyncConnection, workspace_id: str) -> dict[str, Any] | None:
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            "SELECT * FROM student_profiles WHERE workspace_id = %s",
            (workspace_id,),
        )
        return await cur.fetchone()


async def save_marks(conn: AsyncConnection, workspace_id: str, maths: int, physics: int, chemistry: int) -> dict[str, Any]:
    cutoff = int(round(maths + (physics / 2) + (chemistry / 2)))
    eligible = cutoff >= 90
    reason = None if eligible else "TNEA counselling usually requires a 90/200 cutoff. You can still browse colleges, but recommendations and choice filing stay locked."
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            INSERT INTO student_profiles (workspace_id, maths_mark, physics_mark, chemistry_mark, cutoff_mark, expected_cutoff_mark)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (workspace_id) DO UPDATE SET
                maths_mark = EXCLUDED.maths_mark,
                physics_mark = EXCLUDED.physics_mark,
                chemistry_mark = EXCLUDED.chemistry_mark,
                cutoff_mark = EXCLUDED.cutoff_mark,
                expected_cutoff_mark = EXCLUDED.expected_cutoff_mark,
                updated_at = now()
            """,
            (workspace_id, maths, physics, chemistry, cutoff, cutoff),
        )
        await cur.execute(
            """
            INSERT INTO onboarding_state (workspace_id, current_step, is_complete, eligible, eligibility_reason, last_route)
            VALUES (%s, %s, false, %s, %s, %s)
            ON CONFLICT (workspace_id) DO UPDATE SET
                current_step = %s,
                eligible = EXCLUDED.eligible,
                eligibility_reason = EXCLUDED.eligibility_reason,
                last_route = EXCLUDED.last_route,
                updated_at = now()
            RETURNING workspace_id, current_step, is_complete, eligible, eligibility_reason
            """,
            (workspace_id, 2, eligible, reason, "/onboarding/details", 2),
        )
        state = await cur.fetchone()
    await conn.commit()
    return {**state, "cutoff_mark": cutoff}


async def save_details(conn: AsyncConnection, workspace_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            UPDATE student_profiles SET
                full_name = %s,
                board = %s,
                district = %s,
                home_district = %s,
                community_quota = %s,
                updated_at = now()
            WHERE workspace_id = %s
            """,
            (
                payload["full_name"],
                payload["board"],
                payload["district"],
                payload["home_district"],
                payload["community_quota"],
                workspace_id,
            ),
        )
        await cur.execute(
            """
            INSERT INTO onboarding_state (workspace_id, current_step, is_complete, last_route)
            VALUES (%s, %s, true, %s)
            ON CONFLICT (workspace_id) DO UPDATE SET
                current_step = %s,
                is_complete = true,
                last_route = EXCLUDED.last_route,
                completed_at = COALESCE(onboarding_state.completed_at, now()),
                updated_at = now()
            RETURNING workspace_id, current_step, is_complete, eligible, eligibility_reason
            """,
            (workspace_id, 3, "/onboarding/rank", 3),
        )
        state = await cur.fetchone()
        await cur.execute("SELECT cutoff_mark FROM student_profiles WHERE workspace_id = %s", (workspace_id,))
        profile = await cur.fetchone()
    await conn.commit()
    return {**state, "cutoff_mark": profile["cutoff_mark"] if profile else None}


def calculate_aggregate_mark(maths: int, physics: int, chemistry: int) -> int:
    return int(round(maths + (physics / 2) + (chemistry / 2)))


async def fetch_rank_band(conn: AsyncConnection, maths: int, physics: int, chemistry: int) -> dict[str, Any] | None:
    aggregate_mark = calculate_aggregate_mark(maths, physics, chemistry)
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            SELECT aggregate_mark, rank_min, rank_max,
                   confidence_label, sample_size, source_years, is_abstain
            FROM rank_lookup
            WHERE aggregate_mark = %s
            """,
            (aggregate_mark,),
        )
        return await cur.fetchone()


def compute_safety(student_rank: int | None, cutoff_rank: int | None) -> str | None:
    if student_rank is None or cutoff_rank is None:
        return None
    if student_rank <= cutoff_rank - 500:
        return "safe"
    if abs(student_rank - cutoff_rank) <= 500:
        return "moderate"
    return "ambitious"


async def fetch_recommendations(conn: AsyncConnection, workspace_id: str, paid: bool) -> dict[str, Any]:
    profile = await get_student_profile(conn, workspace_id)
    if not profile or not profile.get("community_quota"):
        return {"items": [], "total": 0, "returned": 0, "paid": paid, "restriction": None}

    if not await dataset_is_verified(conn, "cutoff_data"):
        return {"items": [], "total": 0, "returned": 0, "paid": paid, "restriction": "data_not_ready"}

    student_rank = profile.get("official_rank")
    if student_rank is None and profile.get("maths_mark") is not None:
        band = await fetch_rank_band(conn, profile["maths_mark"], profile["physics_mark"], profile["chemistry_mark"])
        if band and not band["is_abstain"]:
            student_rank = band["rank_max"]

    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            WITH latest AS (SELECT max(season_year) AS season_year FROM cutoff_data),
            cutoffs AS (
                SELECT cd.college_code, cd.branch_code, max(cd.general_rank) AS cutoff_rank, max(cd.season_year) AS season_year
                FROM cutoff_data cd, latest
                WHERE cd.season_year = latest.season_year
                  AND cd.community_quota = %s
                  AND cd.general_rank IS NOT NULL
                GROUP BY cd.college_code, cd.branch_code
            )
            SELECT c.college_code, c.college_name, b.branch_code, b.branch_name,
                   c.district, cutoffs.cutoff_rank, cutoffs.season_year
            FROM cutoffs
            JOIN colleges c ON c.college_code = cutoffs.college_code
            JOIN branches b ON b.branch_code = cutoffs.branch_code
            ORDER BY abs(cutoffs.cutoff_rank - COALESCE(%s, cutoffs.cutoff_rank)), c.college_name, b.branch_name
            LIMIT %s
            """,
            (profile["community_quota"], student_rank, 200 if paid else 10),
        )
        rows = await cur.fetchall()
        await cur.execute(
            "SELECT count(*) AS count FROM (SELECT DISTINCT college_code, branch_code FROM cutoff_data WHERE community_quota = %s) x",
            (profile["community_quota"],),
        )
        count_row = await cur.fetchone()

    items = []
    for row in rows:
        item = dict(row)
        item["safety"] = compute_safety(student_rank, row["cutoff_rank"])
        item["is_locked"] = False
        items.append(item)
    total = int(count_row["count"] if count_row else len(items))
    return {"items": items, "total": total, "returned": len(items), "paid": paid, "restriction": None if paid or total <= 10 else "plan_limit"}


async def list_choices(conn: AsyncConnection, workspace_id: str, paid: bool) -> dict[str, Any]:
    limit = 200 if paid else 20
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            SELECT ucp.id, ucp.priority, ucp.college_code, c.college_name,
                   ucp.branch_code, b.branch_name, c.district,
                   ucp.system_category, ucp.manual_category, ucp.notes
            FROM user_college_preferences ucp
            LEFT JOIN colleges c ON c.college_code = ucp.college_code
            LEFT JOIN branches b ON b.branch_code = ucp.branch_code
            WHERE ucp.workspace_id = %s AND ucp.preference_group = %s AND ucp.active = true
            ORDER BY ucp.priority, ucp.created_at
            LIMIT %s
            """,
            (workspace_id, "primary", limit),
        )
        rows = await cur.fetchall()
    return {"items": rows, "limit": limit, "paid": paid}


async def add_choice(conn: AsyncConnection, workspace_id: str, paid: bool, payload: dict[str, Any]) -> dict[str, Any]:
    limit = 200 if paid else 20
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            "SELECT count(*) AS count, COALESCE(max(priority), 0) AS max_priority FROM user_college_preferences WHERE workspace_id = %s AND preference_group = %s AND active = true",
            (workspace_id, "primary"),
        )
        count_row = await cur.fetchone()
        if count_row and int(count_row["count"]) >= limit:
            raise ValueError("choice limit reached")
        next_priority = int(count_row["max_priority"] if count_row else 0) + 1
        await cur.execute(
            """
            INSERT INTO user_college_preferences
                (workspace_id, preference_group, priority, college_code, branch_code, manual_category, notes, added_from)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (workspace_id, preference_group, college_code, branch_code) DO UPDATE SET
                active = true,
                priority = EXCLUDED.priority,
                manual_category = EXCLUDED.manual_category,
                notes = EXCLUDED.notes,
                updated_at = now()
            """,
            (workspace_id, "primary", next_priority, payload["college_code"], payload["branch_code"], payload.get("manual_category"), payload.get("notes"), "manual"),
        )
    await conn.commit()
    return await list_choices(conn, workspace_id, paid)


async def fetch_profile(conn: AsyncConnection, workspace_id: str, paid: bool) -> dict[str, Any]:
    profile = await get_student_profile(conn, workspace_id) or {}
    return {
        "workspace_id": workspace_id,
        "full_name": profile.get("full_name"),
        "board": profile.get("board"),
        "district": profile.get("district"),
        "home_district": profile.get("home_district"),
        "community_quota": profile.get("community_quota"),
        "maths_mark": profile.get("maths_mark"),
        "physics_mark": profile.get("physics_mark"),
        "chemistry_mark": profile.get("chemistry_mark"),
        "cutoff_mark": profile.get("cutoff_mark"),
        "official_rank": profile.get("official_rank"),
        "paid": paid,
    }


async def update_profile(conn: AsyncConnection, workspace_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            INSERT INTO student_profiles (workspace_id, full_name, board, district, home_district, community_quota)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (workspace_id) DO UPDATE SET
                full_name = EXCLUDED.full_name,
                board = EXCLUDED.board,
                district = EXCLUDED.district,
                home_district = EXCLUDED.home_district,
                community_quota = EXCLUDED.community_quota,
                updated_at = now()
            """,
            (workspace_id, payload.get("full_name"), payload.get("board"), payload.get("district"), payload.get("home_district"), payload.get("community_quota")),
        )
    await conn.commit()
    return await fetch_profile(conn, workspace_id, False)


async def fetch_college_detail(conn: AsyncConnection, college_code: str) -> dict[str, Any] | None:
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            SELECT college_code, college_name, district, autonomous_status, hostel_boys,
                   hostel_girls, transport_facilities, latitude, longitude, address, website, email
            FROM colleges
            WHERE college_code = %s
            """,
            (college_code,),
        )
        college = await cur.fetchone()
        if not college:
            return None
        await cur.execute(
            """
            SELECT cb.branch_code, COALESCE(cb.branch_name, b.branch_name) AS branch_name, cs.total AS total_seats
            FROM college_branches cb
            LEFT JOIN branches b ON b.branch_code = cb.branch_code
            LEFT JOIN community_seats cs ON cs.college_code = cb.college_code AND cs.branch_code = cb.branch_code
            WHERE cb.college_code = %s AND cb.active = true
            ORDER BY branch_name
            LIMIT 80
            """,
            (college_code,),
        )
        branches = await cur.fetchall()
    return {**college, "branches": branches}


async def search_colleges(conn: AsyncConnection, query: str | None, district: str | None, limit: int = 50) -> dict[str, Any]:
    clauses = ["is_architecture = false"]
    params: list[Any] = []
    if query:
        clauses.append("(college_name ILIKE %s OR college_code ILIKE %s)")
        needle = "%" + query + "%"
        params.extend([needle, needle])
    if district:
        clauses.append("district ILIKE %s")
        params.append(district)
    where_sql = " AND ".join(clauses)
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            SELECT college_code, college_name, district, autonomous_status,
                   hostel_boys, hostel_girls, transport_facilities, latitude, longitude
            FROM colleges
            WHERE """ + where_sql + """
            ORDER BY college_name
            LIMIT %s
            """,
            (*params, limit),
        )
        items = await cur.fetchall()
        await cur.execute("SELECT count(*) AS count FROM colleges WHERE " + where_sql, tuple(params))
        count_row = await cur.fetchone()
    return {"items": items, "total": int(count_row["count"] if count_row else len(items))}


async def move_choice(conn: AsyncConnection, workspace_id: str, paid: bool, choice_id: str, priority: int) -> dict[str, Any]:
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            UPDATE user_college_preferences
            SET priority = %s, updated_at = now()
            WHERE id = %s AND workspace_id = %s AND preference_group = %s AND active = true
            """,
            (priority, choice_id, workspace_id, "primary"),
        )
    await conn.commit()
    return await list_choices(conn, workspace_id, paid)


async def update_choice(conn: AsyncConnection, workspace_id: str, paid: bool, choice_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            UPDATE user_college_preferences
            SET notes = %s, manual_category = %s, updated_at = now()
            WHERE id = %s AND workspace_id = %s AND preference_group = %s AND active = true
            """,
            (payload.get("notes"), payload.get("manual_category"), choice_id, workspace_id, "primary"),
        )
    await conn.commit()
    return await list_choices(conn, workspace_id, paid)


async def remove_choice(conn: AsyncConnection, workspace_id: str, paid: bool, choice_id: str) -> dict[str, Any]:
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            UPDATE user_college_preferences
            SET active = false, updated_at = now()
            WHERE id = %s AND workspace_id = %s AND preference_group = %s
            """,
            (choice_id, workspace_id, "primary"),
        )
    await conn.commit()
    return await list_choices(conn, workspace_id, paid)
