# Features
 1. Notion was okay. But now the most important thing I need is my note system to work together with vibe coding. So I need a local-first, plain-text-based solution. Notion is exactly the opposite.
 2. Basically, Obsidian is markdown with links, able to visualize structure as a graph. This is indeed what I want; I seldom enjoy Notion's tree structure.
 4. Canvas is also what I wanted. Embed media, notes, and text, and draw arrows between them. Supports free-hand drawing (or drawing with an extension).

 I would say it should exist as a VSCode extension instead of an application: [Deprecating Obsidian and OpenClaw](../log/2026-05-18.md#deprecating-obsidian-and-openclaw)


# Plugins & Ecosystem
 1. **Superior Extendability:** This is the most important feature for advanced usage.
 2. **Cost-Effective Sync:** The app is basically free, and official sync is $4/month. Since an Obsidian vault is just a folder of markdown files, I can also sync via GitHub.
    - **Cross-Platform:** Obsidian plugins are written in JavaScript, meaning they are 100% identical and compatible across Windows, Linux, and Android.
    - **Git Syncing:** It is highly recommended to commit the `.obsidian/plugins/` folder and `community-plugins.json` to Git. This ensures your phone instantly downloads the exact same plugins and settings as your computer. It is the same across windows linux and android since the plugins are like chrome plugins. but we need to git ignore graph.json and data.json to avoid conflicts
    - **Android Git Setup:** The mobile Git plugin cannot use SSH. You must use HTTPS and a GitHub Personal Access Token (PAT) with `Contents: Read and write` permissions. Clone into an empty vault to sync to mobile.
 3. **Schedule Management:** All task categories ("urgent", "free", "fixed", and "float") can be managed using the **Tasks** plugin. This allows "urgent/free" tasks to be viewed as lists, while "fixed/float" tasks can be scheduled. Crucially, the Tasks plugin automatically timestamps when *any* task is completed, allowing even "free" tasks to show up on the calendar on the day they were finished, seamlessly cross-linking with my daily logs.

## Task Management Workflow
**1. Creating or Editing a Task**
- Place your cursor on the line you want to edit (or on a blank line for a new task).
- Press `Ctrl + P` (or `Cmd + P` on Mac) to open the command palette.
- Type `Tasks: Create or edit task` and hit Enter. Just specify a rough start time and specify it in detail with day planner GUI.
- *Tip:* When you finish a task, just click the checkbox. The plugin automatically appends the completion date!
Notice that recurring tasks creates the next task only on the previous is completed, after which we can see that on day planner.
A simple task is inlined in one log entry, if its details needs to be documented, it should have its own .md, and linking to date logs for tracking creation and completion dates.

**2. Viewing Tasks**
- **Dashboards:** `todo/upcoming.md` (for tasks due/scheduled soon), `todo/free.md` (for your backlog), and `todo/completed.md` (for finished tasks) use the Tasks plugin's query DSL to show aggregated lists.
- **Time-Blocking & Calendar:** Use the **Day Planner** (which depends on dataview) plugin. It integrates perfectly with the Tasks plugin and daily logs, allowing you to drag tasks into specific hourly time slots and navigate your days visually.

# Tips
Making the log/ folder flat is a very common and highly recommended practice in Obsidian, especially if you are using the YYYY-MM-DD naming convention!


Does it impact performance?
No, a flat structure does not negatively impact performance in Obsidian. Obsidian's performance is tied to the total number of files in your vault and the plugins you are running, not how those files are organized into folders. Whether you have 10,000 files in one folder or spread across 1,000 nested folders, Obsidian indexes them the exact same way.

Why a flat log/ folder is better:
Searchability: When you type 2026-05 in Obsidian's quick switcher or search, all your May 2026 logs will instantly pop up in chronological order.
Less Friction: You don't have to click through log > 2026 > May just to find a note.
Graph View: As you noticed, file names are the source of truth in the graph. A flat structure forces you to use descriptive file names (like 2026-05-07.md), which makes your graph view perfectly readable.