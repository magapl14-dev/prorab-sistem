# Graph Report - prorab-sistem  (2026-08-26)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 763 nodes · 1684 edges · 74 communities (64 shown, 10 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 111 edges (avg confidence: 0.86)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `553c63a9`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Community 0
- Community 1
- Community 2
- Community 3
- Community 4
- Community 5
- Community 6
- Community 7
- Community 8
- Community 9
- Community 10
- Community 11
- Community 12
- Community 13
- Community 14
- Community 15
- Community 16
- Community 17
- Community 18
- Community 19
- Community 20
- Community 21
- Community 22
- Community 23
- Community 24
- Community 25
- Community 27
- Community 28
- Community 29
- Community 30
- Community 31
- Community 32
- Community 33
- Community 34
- Community 52
- Community 53
- Community 54
- Community 68
- Community 69
- Community 70
- Community 71
- Community 72
- Community 73

## God Nodes (most connected - your core abstractions)
1. `User` - 82 edges
2. `Base` - 28 edges
3. `esc()` - 25 edges
4. `get_db()` - 18 edges
5. `has_permission()` - 15 edges
6. `Project` - 14 edges
7. `current_user()` - 14 edges
8. `login()` - 14 edges
9. `require_permission()` - 13 edges
10. `fmt()` - 13 edges

## Surprising Connections (you probably didn't know these)
- `test_shim_registers_all_tables()` --uses--> `User`  [INFERRED]
  backend/tests/test_god_files_shim.py → backend/app/models/user.py
- `db_engine()` --uses--> `Base`  [INFERRED]
  backend/tests/conftest.py → backend/app/core/database.py
- `create_dictionary()` --calls--> `Dictionary`  [INFERRED]
  backend/app/api/v1/admin/projects.py → backend/app/models/catalog.py
- `set_master_visibility()` --calls--> `MasterProjectVisibility`  [INFERRED]
  backend/app/api/v1/masters.py → backend/app/models/master.py
- `add_master_rate()` --calls--> `MasterRate`  [INFERRED]
  backend/app/api/v1/masters.py → backend/app/models/master.py

## Import Cycles
- None detected.

## Communities (74 total, 10 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.16
Nodes (17): Base, AppSetting, AuditLog, Dictionary, MasterProjectVisibility, MasterRate, Shim: keep `from app.models.models import X` after the domain split., Photo (+9 more)

### Community 1 - "Community 1"
Cohesion: 0.06
Nodes (71): _all_role_names(), get_permissions(), AsyncSession, get, patch, update_permissions(), activate_project(), assign_user() (+63 more)

### Community 2 - "Community 2"
Cohesion: 0.08
Nodes (46): get_upload_url(), BaseModel, UserAnalyticsRow, AppSettingOut, AppSettingUpdate, BitrixSettingsUpdate, BitrixTestResult, DictionaryCreate (+38 more)

### Community 3 - "Community 3"
Cohesion: 0.05
Nodes (27): ACTION_LABELS, _addFormSnapshot(), _attachDraftListeners(), checkGoalReached(), _defaultsKey(), dictionaries, _Drafts, evalFormula() (+19 more)

### Community 4 - "Community 4"
Cohesion: 0.05
Nodes (42): @capacitor/android, @capacitor/app, @capacitor/camera, @capacitor/cli, @capacitor-community/speech-recognition, @capacitor/core, @capacitor/filesystem, @capacitor/ios (+34 more)

### Community 5 - "Community 5"
Cohesion: 0.11
Nodes (35): confirm_upload(), delete_photo(), _make_thumbnail(), AsyncSession, delete, post, UUID, create_record() (+27 more)

### Community 6 - "Community 6"
Cohesion: 0.15
Nodes (33): add_master_rate(), _assemble_outs(), _build_out(), create_master(), delete_master(), delete_master_rate(), get_master(), list_master_rates() (+25 more)

### Community 7 - "Community 7"
Cohesion: 0.12
Nodes (25): Any, get_bitrix_settings(), AsyncSession, get, patch, post, _row(), test_bitrix_connection() (+17 more)

### Community 8 - "Community 8"
Cohesion: 0.19
Nodes (26): add_comment(), _comment_out(), create_task(), delete_comment(), delete_task(), get_task(), list_assignable_users(), list_comments() (+18 more)

### Community 9 - "Community 9"
Cohesion: 0.24
Nodes (21): all_earnings(), chart14(), _get_user_project(), monthly_breakdown(), period_stats(), project_earnings(), project_plan(), AsyncSession (+13 more)

### Community 10 - "Community 10"
Cohesion: 0.18
Nodes (19): change_pin(), login(), me(), AsyncSession, get, post, Request, refresh() (+11 more)

### Community 11 - "Community 11"
Cohesion: 0.13
Nodes (21): Admin, AI, API_BASE, Auth, _buildUrl(), _cacheGet(), _cacheSet(), _delete() (+13 more)

### Community 12 - "Community 12"
Cohesion: 0.13
Nodes (22): animateEarning(), esc(), fmt(), loadDashboard(), loadHome(), _loadMasterSuggest(), _loadProjectMastersVisibility(), loadReport() (+14 more)

### Community 13 - "Community 13"
Cohesion: 0.15
Nodes (13): _analyticsRangeParams(), applyMoodTint(), calcStreakFromRecords(), loadDictionaries(), loadMotivation(), _renderAnalytics(), renderProjectSelect(), roleLabel() (+5 more)

### Community 14 - "Community 14"
Cohesion: 0.24
Nodes (10): _fixAllAudiosIn(), _fixAudioDuration(), _formatDuration(), _onVoiceStop(), _refreshCmtAttUI(), _refreshTaskAttachmentsUI(), _stopNativeVoiceRec(), _tgInitState() (+2 more)

### Community 15 - "Community 15"
Cohesion: 0.20
Nodes (9): background_color, description, display, icons, name, orientation, short_name, start_url (+1 more)

### Community 16 - "Community 16"
Cohesion: 0.33
Nodes (5): androidx.test.ext.junit.runners.AndroidJUnit4, ExampleInstrumentedTest, ExampleUnitTest, org.junit.runner.RunWith, org.junit.Test

### Community 19 - "Community 19"
Cohesion: 0.25
Nodes (5): count, DST, fs, path, SRC

### Community 21 - "Community 21"
Cohesion: 0.33
Nodes (7): _dateMatches(), formatDate(), loadTab(), renderMasterCards(), renderRecords(), renderRecordsCards(), rerenderRecList()

### Community 22 - "Community 22"
Cohesion: 0.47
Nodes (4): do_run_migrations(), run_async_migrations(), run_migrations_online(), Connection

### Community 23 - "Community 23"
Cohesion: 0.40
Nodes (4): _files(), Path, S6: mobile/www — копия frontend; сборка Capacitor зовёт sync-web., test_sync_web_mirrors_frontend_and_sw_version()

### Community 24 - "Community 24"
Cohesion: 0.33
Nodes (6): loadTasks(), renderTaskList(), _taskDateRange(), _taskDueText(), _taskPriorityBadge(), _updateTaskCounters()

### Community 25 - "Community 25"
Cohesion: 0.40
Nodes (5): AsyncSession, datetime, get, Аналитика по пользователям: кто что внёс. Возвращает по каждому активному…, users_analytics()

### Community 27 - "Community 27"
Cohesion: 0.40
Nodes (5): applyBranding(), applyPrimaryColor(), _hexToRgb(), _rgbToHex(), _shade()

### Community 28 - "Community 28"
Cohesion: 0.60
Nodes (5): attachMic(), scanAndAttach(), startNative(), startWeb(), stopActive()

### Community 29 - "Community 29"
Cohesion: 0.40
Nodes (5): _grokStartRec(), _grokVoiceFillCommon(), openModal(), _syncAIStatus(), _updateVoiceIndicators()

### Community 34 - "Community 34"
Cohesion: 0.83
Nodes (3): gradlew script, die(), warn()

### Community 54 - "Community 54"
Cohesion: 0.67
Nodes (3): _legacyStartVoiceForm(), parseVoiceCommand(), resetVoiceBtn()

### Community 69 - "Community 69"
Cohesion: 0.12
Nodes (23): RolePermission, client(), db_engine(), db_session(), fake_redis(), hash_pin(), _jsonb_sqlite(), login() (+15 more)

### Community 70 - "Community 70"
Cohesion: 0.16
Nodes (16): logout(), HTTPAuthorizationCredentials, current_user(), AsyncSession, HTTPAuthorizationCredentials, close_redis(), get_redis(), create_access_token() (+8 more)

### Community 71 - "Community 71"
Cohesion: 0.46
Nodes (5): Голосовое заполнение форм через xAI Grok. Логика: фронт записывает голосовое…, get_db(), FastAPI dependency: 403 if user lacks the permission., require_permission(), FastAPI

### Community 72 - "Community 72"
Cohesion: 0.47
Nodes (6): _get_or_create(), get_settings(), AsyncSession, get, patch, update_settings()

### Community 73 - "Community 73"
Cohesion: 0.67
Nodes (3): ai_health(), get, Публичный статус: активен ли Grok. Фронт по нему рисует индикатор рядом с…

## Knowledge Gaps
- **62 isolated node(s):** `Admin`, `AI`, `API_BASE`, `Auth`, `Earnings` (+57 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **10 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `User` connect `Community 1` to `Community 0`, `Community 2`, `Community 5`, `Community 6`, `Community 7`, `Community 72`, `Community 9`, `Community 10`, `Community 8`, `Community 70`, `Community 69`, `Community 25`?**
  _High betweenness centrality (0.085) - this node is a cross-community bridge._
- **Why does `_NullRedis` connect `Community 17` to `Community 70`?**
  _High betweenness centrality (0.012) - this node is a cross-community bridge._
- **Why does `FakeRedis` connect `Community 18` to `Community 69`?**
  _High betweenness centrality (0.010) - this node is a cross-community bridge._
- **Are the 4 inferred relationships involving `User` (e.g. with `main()` and `seed()`) actually correct?**
  _`User` has 4 INFERRED edges - model-reasoned connections that need verification._
- **Are the 48 inferred relationships involving `HTTPException` (e.g. with `update_permissions()` and `activate_project()`) actually correct?**
  _`HTTPException` has 48 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Admin`, `AI`, `API_BASE` to the rest of the system?**
  _62 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Community 1` be split into smaller, more focused modules?**
  _Cohesion score 0.05964912280701754 - nodes in this community are weakly interconnected._