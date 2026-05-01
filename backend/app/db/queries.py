"""Database query helpers for the P0 Counsly API."""

from decimal import Decimal, ROUND_FLOOR
from typing import Any

from psycopg import AsyncConnection
from psycopg.rows import dict_row

from app.config import settings


def _scalar_config(value: Any) -> Any:
    return value


def _stringify_workspace_id(payload: dict[str, Any] | None) -> dict[str, Any] | None:
    if not payload or payload.get("workspace_id") is None:
        return payload
    return {**payload, "workspace_id": str(payload["workspace_id"])}


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
                      AND s.season_year = %s
                      AND s.status = %s
                      AND (s.ends_at IS NULL OR s.ends_at > now())
                ) AS paid
            FROM app_users au
            JOIN auth_identities ai ON ai.id = au.auth_identity_id
            JOIN workspaces w ON w.app_user_id = au.id
            WHERE au.id = %s AND au.status = %s
            """,
            (settings.season_year, "active", app_user_id, "active"),
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
    return _stringify_workspace_id({**state, "cutoff_mark": cutoff})


async def save_details(conn: AsyncConnection, workspace_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            "SELECT 1 FROM student_profiles WHERE workspace_id = %s AND maths_mark IS NOT NULL AND physics_mark IS NOT NULL AND chemistry_mark IS NOT NULL",
            (workspace_id,),
        )
        if not await cur.fetchone():
            raise LookupError("marks required")
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
    return _stringify_workspace_id({**state, "cutoff_mark": profile["cutoff_mark"] if profile else None})


async def fetch_rank_band(conn: AsyncConnection, aggregate_mark: Decimal) -> dict[str, Any] | None:
    """Fetch rank band for a specific aggregate mark."""
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


async def workspace_is_eligible(conn: AsyncConnection, workspace_id: str) -> bool:
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            "SELECT eligible FROM onboarding_state WHERE workspace_id = %s",
            (workspace_id,),
        )
        row = await cur.fetchone()
    return bool(row and row["eligible"])


async def fetch_recommendations(conn: AsyncConnection, workspace_id: str, paid: bool) -> dict[str, Any]:
    profile = await get_student_profile(conn, workspace_id)
    if not profile or not profile.get("community_quota"):
        return {"items": [], "total": 0, "returned": 0, "paid": paid, "restriction": None}

    if not await workspace_is_eligible(conn, workspace_id):
        return {"items": [], "total": 0, "returned": 0, "paid": paid, "restriction": "ineligible"}

    student_rank = profile.get("official_rank")
    if student_rank is None and profile.get("maths_mark") is not None:
        band = await fetch_rank_band(
            conn,
            profile["maths_mark"],
            profile["physics_mark"],
            profile["chemistry_mark"],
            profile.get("community_quota"),
        )
        if band and not band["is_abstain"]:
            student_rank = band["rank_max"]

    limit = 200 if paid else 10
    async with conn.cursor(row_factory=dict_row) as cur:
        if not await dataset_is_verified(conn, "cutoff_data"):
            return {"items": [], "total": 0, "returned": 0, "paid": paid, "restriction": "data_not_ready"}
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
            LEFT JOIN seat_matrix_current sm ON sm.college_code = cutoffs.college_code AND sm.branch_code = cutoffs.branch_code
            WHERE (NOT EXISTS (SELECT 1 FROM seat_matrix_current) OR COALESCE(sm.total, 0) > 0)
            ORDER BY
                CASE
                    WHEN %s IS NULL THEN cutoffs.cutoff_rank
                    ELSE abs(cutoffs.cutoff_rank - %s)
                END,
                c.college_name,
                b.branch_name
            LIMIT %s
            """,
            (profile["community_quota"], student_rank, student_rank, limit),
        )
        rows = await cur.fetchall()
        await cur.execute(
            """
            SELECT count(*) AS count
            FROM (
                SELECT DISTINCT cd.college_code, cd.branch_code
                FROM cutoff_data cd
                CROSS JOIN (SELECT max(season_year) AS season_year FROM cutoff_data) latest
                LEFT JOIN seat_matrix_current sm ON sm.college_code = cd.college_code AND sm.branch_code = cd.branch_code
                WHERE cd.season_year = latest.season_year
                  AND cd.community_quota = %s
                  AND (NOT EXISTS (SELECT 1 FROM seat_matrix_current) OR COALESCE(sm.total, 0) > 0)
            ) x
            """,
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
    if not await workspace_is_eligible(conn, workspace_id):
        raise ValueError("ineligible")
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            "SELECT count(*) AS count, COALESCE(max(priority), 0) AS max_priority FROM user_college_preferences WHERE workspace_id = %s AND preference_group = %s AND active = true",
            (workspace_id, "primary"),
        )
        count_row = await cur.fetchone()
        if count_row and int(count_row["count"]) >= limit:
            raise ValueError("choice limit reached")
        await cur.execute(
            """
            SELECT
                NOT EXISTS (SELECT 1 FROM seat_matrix_current)
                OR EXISTS (
                    SELECT 1
                    FROM seat_matrix_current
                    WHERE college_code = %s AND branch_code = %s AND total > 0
                ) AS available
            """,
            (payload["college_code"], payload["branch_code"]),
        )
        availability = await cur.fetchone()
        if availability and not availability["available"]:
            raise ValueError("choice unavailable")
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
            SELECT college_code, college_name, district, taluk, pincode, phone_fax,
                   autonomous_status, minority_status, placement_record,
                   hostel_boys, hostel_girls, transport_facilities,
                   min_transport_charges, max_transport_charges,
                   latitude, longitude, maps_url, address, website, email,
                   raw_payload
            FROM colleges
            WHERE college_code = %s
            """,
            (college_code,),
        )
        college = await cur.fetchone()
        if not college:
            return None

        # Extract rich fields from raw_payload JSONB
        raw = college.pop("raw_payload", None) or {}
        college["nearest_railway_station"] = raw.get("Nearest_Railway_Station")
        college["distance_from_railway_km"] = raw.get("Distance_in_KMS_from_Nearest_Railway_Station")
        college["distance_from_dist_hq_km"] = raw.get("Distance_in_KMS_from_Dist_HQ")
        college["dean_principal"] = raw.get("Dean_Principal")
        college["anti_ragging_phone"] = str(raw.get("Anti_Ragging_Phone_No", "")) or None
        college["type_of_mess"] = raw.get("Type_of_Mess")
        college["room_rent"] = raw.get("Room_Rent")
        college["hostel_boys_type"] = raw.get("Hostel_Boys_Permanent_or_Rental")
        college["hostel_girls_type"] = raw.get("Hostel_Girls_Permanent_or_Rental")

        await cur.execute(
            """
            SELECT cb.branch_code, COALESCE(cb.branch_name, b.branch_name) AS branch_name, sm.total AS total_seats
            FROM college_branches cb
            LEFT JOIN branches b ON b.branch_code = cb.branch_code
            LEFT JOIN seat_matrix_current sm ON sm.college_code = cb.college_code AND sm.branch_code = cb.branch_code
            WHERE cb.college_code = %s AND cb.active = true
              AND (NOT EXISTS (SELECT 1 FROM seat_matrix_current) OR COALESCE(sm.total, 0) > 0)
            ORDER BY branch_name
            LIMIT 80
            """,
            (college_code,),
        )
        branches = await cur.fetchall()

        await cur.execute(
            """
            SELECT branch_code, community_quota, MAX(general_rank) AS closing_rank,
                   MAX(aggregate_mark) AS closing_mark, season_year, round_number
            FROM cutoff_data
            WHERE college_code = %s
            GROUP BY branch_code, community_quota, season_year, round_number
            ORDER BY season_year DESC, round_number DESC
            LIMIT 200
            """,
            (college_code,),
        )
        cutoffs = await cur.fetchall()

    return {**college, "branches": branches, "cutoffs": cutoffs}


async def search_colleges(conn: AsyncConnection, query: str | None, district: str | None, limit: int = 50) -> dict[str, Any]:
    clauses = ["is_architecture = false"]
    params: list[Any] = []
    if query:
        clauses.append("(college_name ILIKE %s ESCAPE '\\' OR college_code ILIKE %s ESCAPE '\\')")
        escaped_query = query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        needle = "%" + escaped_query + "%"
        params.extend([needle, needle])
    if district:
        escaped_district = district.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        clauses.append("district ILIKE %s ESCAPE '\\'")
        params.append(escaped_district)
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


async def fetch_districts(conn: AsyncConnection) -> list[str]:
    """Return distinct districts from colleges table, sorted alphabetically."""
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute("SELECT DISTINCT district FROM colleges WHERE district IS NOT NULL ORDER BY district")
        return [row["district"] for row in await cur.fetchall()]


async def move_choice(conn: AsyncConnection, workspace_id: str, paid: bool, choice_id: str, priority: int) -> dict[str, Any]:
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            SELECT id
            FROM user_college_preferences
            WHERE workspace_id = %s AND preference_group = %s AND active = true
            ORDER BY priority, created_at
            """,
            (workspace_id, "primary"),
        )
        ordered_ids = [str(row["id"]) for row in await cur.fetchall()]
        if choice_id not in ordered_ids:
            return await list_choices(conn, workspace_id, paid)
        ordered_ids.remove(choice_id)
        ordered_ids.insert(max(0, min(priority - 1, len(ordered_ids))), choice_id)
        for index, item_id in enumerate(ordered_ids, start=1):
            await cur.execute(
                """
                UPDATE user_college_preferences
                SET priority = %s, updated_at = now()
                WHERE id = %s AND workspace_id = %s AND preference_group = %s AND active = true
                """,
                (index, item_id, workspace_id, "primary"),
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
        await cur.execute(
            """
            WITH ordered AS (
                SELECT id, row_number() OVER (ORDER BY priority, created_at) AS next_priority
                FROM user_college_preferences
                WHERE workspace_id = %s AND preference_group = %s AND active = true
            )
            UPDATE user_college_preferences ucp
            SET priority = ordered.next_priority, updated_at = now()
            FROM ordered
            WHERE ucp.id = ordered.id
            """,
            (workspace_id, "primary"),
        )
    await conn.commit()
    return await list_choices(conn, workspace_id, paid)


# === Chat queries (Storage-backed) ===


async def count_user_messages(conn: AsyncConnection, workspace_id: str) -> int:
    """Count total user messages via conversations.user_message_count (no DB message table)."""
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            SELECT COALESCE(SUM(user_message_count), 0) AS count
            FROM conversations
            WHERE workspace_id = %s
            """,
            (workspace_id,),
        )
        row = await cur.fetchone()
    return int(row["count"]) if row else 0


async def create_conversation(conn: AsyncConnection, workspace_id: str, title: str | None) -> dict[str, Any]:
    """Create a new conversation."""
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            INSERT INTO conversations (workspace_id, title)
            VALUES (%s, %s)
            RETURNING id, title, created_at
            """,
            (workspace_id, title),
        )
        row = await cur.fetchone()
    await conn.commit()
    return {**row, "id": str(row["id"]), "created_at": str(row["created_at"])}


async def list_conversations(conn: AsyncConnection, workspace_id: str) -> list[dict[str, Any]]:
    """List all conversations for a workspace, newest first."""
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            SELECT id, title, created_at
            FROM conversations
            WHERE workspace_id = %s
            ORDER BY updated_at DESC
            LIMIT 50
            """,
            (workspace_id,),
        )
        rows = await cur.fetchall()
    return [{"id": str(r["id"]), "title": r["title"], "created_at": str(r["created_at"])} for r in rows]


async def save_message(conn: AsyncConnection, conversation_id: str, workspace_id: str, role: str, content: str) -> dict[str, Any]:
    """Save a chat message to Supabase Storage JSON and update conversation metadata."""
    from datetime import datetime, timezone

    from app.storage import download_messages, upload_messages

    # Verify ownership
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            "SELECT id FROM conversations WHERE id = %s AND workspace_id = %s",
            (conversation_id, workspace_id),
        )
        if not await cur.fetchone():
            raise LookupError("conversation not found")

    # Download existing messages, append, upload
    messages = await download_messages(workspace_id, conversation_id)
    msg_id = str(len(messages) + 1)
    now = datetime.now(timezone.utc).isoformat()
    new_msg = {"id": msg_id, "role": role, "content": content, "created_at": now}
    messages.append(new_msg)
    await upload_messages(workspace_id, conversation_id, messages)

    # Update conversation metadata in DB
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            "UPDATE conversations SET updated_at = now() WHERE id = %s",
            (conversation_id,),
        )
        if role == "user":
            await cur.execute(
                """
                UPDATE conversations
                SET user_message_count = user_message_count + 1, title = COALESCE(title, %s)
                WHERE id = %s
                """,
                (content[:80], conversation_id),
            )
    await conn.commit()
    return new_msg


async def get_messages(conn: AsyncConnection, conversation_id: str, workspace_id: str, limit: int = 100) -> list[dict[str, Any]]:
    """Get messages from Supabase Storage JSON (verify ownership via conversations table)."""
    from app.storage import download_messages

    # Verify ownership
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            "SELECT id FROM conversations WHERE id = %s AND workspace_id = %s",
            (conversation_id, workspace_id),
        )
        if not await cur.fetchone():
            raise LookupError("conversation not found")

    messages = await download_messages(workspace_id, conversation_id)
    return messages[-limit:]

