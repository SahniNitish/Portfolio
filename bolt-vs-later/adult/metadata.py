"""Titles, descriptions (with chapters + sources), tags and pinned comments for the adult season."""
import json
import os

from . import film

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "output", "adult")
SERIES = "VS LATER"

META = {
    1: ("You're Not Lazy. You're Avoiding Something. | VS LATER Ep. 1",
        "You're not lazy. Procrastination is mood repair: the task feels bad, so you run. Three ways to stop running.",
        ["Sirois & Pychyl (2013), procrastination and short-term mood regulation, Social and Personality Psychology Compass",
         "Joseph Ferrari's estimate that ~20% of adults are chronic procrastinators",
         "Wohl, Pychyl & Bennett (2010), self-forgiveness and procrastination, Personality and Individual Differences"],
        ["why do i procrastinate", "not lazy", "procrastination psychology", "dark motivation"],
        "What feeling are you avoiding right now? Name it below. Then go do two minutes of it."),
    2: ("Starting Is the Whole Fight (The 2-Minute Rule) | VS LATER Ep. 2",
        "The hardest part of anything is the first two minutes. Make the start too small to refuse.",
        ["David Allen, 'Getting Things Done' (two-minute rule)", "James Clear, 'Atomic Habits' (two-minute version of habits)",
         "Zeigarnik (1927) on memory for unfinished tasks"],
        ["2 minute rule", "how to start", "just start", "atomic habits"],
        "Set a 2-minute timer right now. Did you stop when it rang? Be honest."),
    3: ("Your Phone Is Winning. Here's How to Fight Back. | VS LATER Ep. 3",
        "~205 phone checks a day. It's not weakness, it's design. Distance, friction, and a better break.",
        ["Reviews.org (2025) cell phone usage survey",
         "Ward, Duke, Gneezy & Bos (2017), 'Brain Drain', Journal of the Association for Consumer Research"],
        ["doomscrolling", "phone addiction", "screen time", "dopamine detox"],
        "Where does your phone sleep tonight? Wrong answers only."),
    4: ("Perfectionism Is Just Fear in a Suit | VS LATER Ep. 4",
        "High standards aren't the problem. Fear of mistakes is. Messy first drafts, B+ work, and the spotlight effect.",
        ["Sirois, Molnar & Hirsch (2017), meta-analysis of perfectionism and procrastination, European Journal of Personality",
         "Gilovich, Medvec & Savitsky (2000), the spotlight effect, Journal of Personality and Social Psychology"],
        ["perfectionism", "fear of failure", "overthinking", "done is better than perfect"],
        "What have you been 'polishing' for way too long? Ship it today."),
    5: ("Too Much to Do? Do This One Thing First | VS LATER Ep. 5",
        "When everything is urgent, nothing feels possible. Brain dump, pick one, eat the frog.",
        ["2025 study in BMC Psychology on self-reported causes of procrastination",
         "Masicampo & Baumeister (2011), 'Consider it done!', Journal of Personality and Social Psychology"],
        ["overwhelmed", "too much to do", "eat the frog", "prioritize"],
        "What's your frog today? Name it and kill it before noon."),
    6: ("Motivation Is a Lie. Build This Instead. | VS LATER Ep. 6",
        "Motivation is weather. Discipline is climate. Habits take ~66 days on average, and if-then plans help you follow through.",
        ["Lally, van Jaarsveld, Potts & Wardle (2010), 'How are habits formed', European Journal of Social Psychology",
         "Gollwitzer & Sheeran (2006), meta-analysis of implementation intentions (94 independent tests)",
         "James Clear, 'Atomic Habits'"],
        ["no motivation", "discipline", "habits", "66 days", "winter arc"],
        "Write your if-then plan: 'If ____, then I ____.' Day 1 starts now."),
    7: ("You Keep Betraying Your Future Self | VS LATER Ep. 7",
        "Your brain treats future-you like a stranger, so 'later' feels free. Make future-you real.",
        ["Ersner-Hershfield, Wimmer & Knutson (2009), future self-continuity, Social Cognitive and Affective Neuroscience",
         "Hershfield et al. (2011), age-progressed renderings and saving, Journal of Marketing Research",
         "Suzy Welch, '10-10-10'"],
        ["future self", "delayed gratification", "discipline", "self improvement"],
        "One line to your future self. Go."),
    8: ("Always Tired? Burnout Isn't Weakness | VS LATER Ep. 8",
        "Sometimes it isn't procrastination. The tank is empty. Sprints, sleep, and real breaks.",
        ["World Health Organization (2019), burnout as an occupational phenomenon (ICD-11)",
         "Talker Research poll of 2,000 people on young adults' stress",
         "Watson et al. (2015), AASM/SRS adult sleep recommendation", "Francesco Cirillo, the Pomodoro Technique"],
        ["burnout", "always tired", "rest", "pomodoro", "mental health"],
        "What's your real break? No screens allowed. If you're struggling, please talk to someone you trust."),
    9: ("Stop Measuring Your Life Against Strangers | VS LATER Ep. 9",
        "You're comparing your behind-the-scenes to their highlight reel. Race yesterday's you instead.",
        ["Festinger (1954), 'A theory of social comparison processes', Human Relations",
         "1.01^365 = 37.8 (illustrative compounding math)"],
        ["comparison", "stop comparing yourself", "social media", "1 percent better"],
        "Name one way you're better than a year ago. Small counts."),
    10: ("You Failed. Good. Now Never Miss Twice. | VS LATER Ep. 10",
         "One slip barely matters. Missing twice is a new habit. Restart small, learn, and plan for the slip.",
         ["Lally et al. (2010), habit formation and missed days, European Journal of Social Psychology",
          "Wohl, Pychyl & Bennett (2010), self-forgiveness and procrastination", "James Clear, 'Atomic Habits' (never miss twice)"],
         ["failure", "never miss twice", "restart", "resilience", "comeback"],
         "Which habit are you restarting today? Tiny version counts."),
}

COMMON = ["procrastination", "motivation", "discipline", "self improvement", "animated", "psychology", "vs later",
          "how to stop procrastinating", "productivity"]

LABELS = {"title": "Intro", "room": "The trap", "text": "The truth", "stat": "By the numbers", "climb": "The climb",
          "kneel": "Rock bottom", "rise": "Not today", "fight": "The fight", "run": "Momentum", "gym": "The grind",
          "montage": "The grind", "dawn": "Dawn", "end": "Next episode"}


def ts(t):
    t = int(t)
    return f"{t // 60}:{t % 60:02d}"


def chapters(ep):
    out = [(0.0, "Intro")]
    used = {"Intro"}
    for s in ep["shots"]:
        lab = LABELS.get(s["type"], s["type"].title())
        if lab in used:
            continue
        if s["start"] - out[-1][0] >= 10:
            out.append((s["start"], lab))
            used.add(lab)
    return out


def make_all():
    os.makedirs(os.path.join(OUT, "descriptions"), exist_ok=True)
    allm, md = [], [f"# {SERIES}: adult season upload kit", ""]
    for n in range(1, 11):
        ep = film.load(n)
        total, *_ = film.timeline(ep)
        title, hook, sources, tags, pinned = META[n]
        chs = chapters(ep)
        desc = "\n".join([hook, "",
                          "You vs your shadow self, the voice that always says 'later'. A short animated film about the fight you have every day.",
                          "", "CHAPTERS"] + [f"{ts(t)} {lab}" for t, lab in chs] +
                         ["", "SOURCES"] + [f"- {s}" for s in sources] +
                         ["", "New episode every week. Subscribe and start your arc.", "",
                          "Education and motivation only, not medical or mental-health advice.", "",
                          "#procrastination #discipline #motivation #winterarc #vslater"])
        tg = tags + COMMON
        rec = dict(episode=n, file=f"videos/ep{n:02d}.mp4", thumbnail=f"thumbnails/ep{n:02d}_thumbnail.jpg",
                   duration=ts(total), title=title, description=desc, tags=tg, pinned_comment=pinned)
        allm.append(rec)
        with open(os.path.join(OUT, "descriptions", f"ep{n:02d}_description.txt"), "w") as f:
            f.write(f"TITLE:\n{title}\n\nDESCRIPTION:\n{desc}\n\nTAGS:\n{', '.join(tg)}\n\nPINNED COMMENT:\n{pinned}\n")
        md += [f"## Episode {n}: {title}", "", f"- Video: `output/adult/videos/ep{n:02d}.mp4` ({ts(total)})",
               f"- Thumbnail: `output/adult/thumbnails/ep{n:02d}_thumbnail.jpg`", f"- Tags: {', '.join(tg)}",
               f"- Pinned comment: {pinned}", "", "```", desc, "```", ""]
    with open(os.path.join(OUT, "youtube_metadata.json"), "w") as f:
        json.dump(allm, f, indent=2, ensure_ascii=False)
    with open(os.path.join(OUT, "UPLOAD_KIT.md"), "w") as f:
        f.write("\n".join(md))
    return allm
