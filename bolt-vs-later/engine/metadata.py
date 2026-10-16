"""YouTube titles, descriptions (with chapters), tags and pinned comments for every episode."""
import copy
import importlib
import json
import os

from .build import build_timeline

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "output")

CHANNEL = "Bolt vs Later"
TAGLINE = "Beat procrastination, one tiny win at a time."
COMMON_TAGS = ["procrastination", "how to stop procrastinating", "motivation", "productivity", "self improvement",
               "animated explainer", "psychology", "habits", "discipline", "bolt vs later", "cartoon motivation"]

META = {
    1: dict(title="Why You Procrastinate (It's NOT Laziness) | Bolt vs Later Ep. 1",
            hook="You're not lazy. Psychologists say procrastination is mostly about managing bad feelings, not time. Bolt takes on Lord Later with 3 weapons that actually work.",
            sources=["Sirois & Pychyl (2013), 'Procrastination and the priority of short-term mood regulation', Social and Personality Psychology Compass",
                     "Joseph Ferrari's research estimating ~20% of adults are chronic procrastinators",
                     "Wohl, Pychyl & Bennett (2010), 'I forgive myself, now I can study', Personality and Individual Differences"],
            tags=["why do I procrastinate", "procrastination psychology", "not lazy", "emotional regulation", "self forgiveness"],
            pinned="What's the ONE task you've been avoiding? Drop it below and do the tiniest first step today. Bolt believes in you!"),
    2: dict(title="The 2-Minute Rule That Beats Procrastination | Bolt vs Later Ep. 2",
            hook="The hardest part of any task is the first two minutes. Here's how to make starting so easy that procrastination can't argue.",
            sources=["David Allen, 'Getting Things Done' (the two-minute rule)",
                     "James Clear, 'Atomic Habits' (two-minute versions of habits)",
                     "Zeigarnik, B. (1927) on memory for unfinished tasks"],
            tags=["2 minute rule", "how to start", "getting things done", "atomic habits", "zeigarnik effect"],
            pinned="Try it right now: pick one task and do just 2 minutes. Did you keep going? Tell Bolt below!"),
    3: dict(title="How to Stop Doomscrolling: Escape the Phone Trap | Bolt vs Later Ep. 3",
            hook="One 2025 survey says the average American checks their phone ~205 times a day. Bolt's anti-scroll toolkit helps you take your time back.",
            sources=["Reviews.org (2025) cell phone usage survey",
                     "Ward, Duke, Gneezy & Bos (2017), 'Brain Drain', Journal of the Association for Consumer Research"],
            tags=["doomscrolling", "phone addiction", "screen time", "digital detox", "social media addiction"],
            pinned="Mission check: did your phone sleep outside your bedroom last night? How did your morning feel?"),
    4: dict(title="Perfectionism Is Secretly Procrastination | Bolt vs Later Ep. 4",
            hook="High standards aren't the problem. Fear of mistakes is. Learn the B+ rule, the messy first draft, and the spotlight check.",
            sources=["Sirois, Molnar & Hirsch (2017), meta-analysis of perfectionism and procrastination, European Journal of Personality",
                     "Gilovich, Medvec & Savitsky (2000), the spotlight effect, Journal of Personality and Social Psychology"],
            tags=["perfectionism", "fear of failure", "done is better than perfect", "spotlight effect", "overthinking"],
            pinned="What did you ship at B+ level today? Brag about it below. Done beats perfect!"),
    5: dict(title="Too Much To Do? Do THIS First (Beat Overwhelm) | Bolt vs Later Ep. 5",
            hook="When everything feels urgent, nothing feels startable. Bolt's 3-step escape plan: brain dump, pick one, eat the frog.",
            sources=["2025 study in BMC Psychology on self-reported causes of procrastination",
                     "Masicampo & Baumeister (2011), 'Consider it done!', Journal of Personality and Social Psychology",
                     "Rubinstein, Meyer & Evans (2001), task-switching costs, Journal of Experimental Psychology"],
            tags=["overwhelmed", "too much to do", "eat the frog", "brain dump", "prioritization", "multitasking"],
            pinned="What's your frog today? Name it below, then go eat it first!"),
    6: dict(title="Stop Waiting for Motivation (Do This Instead) | Bolt vs Later Ep. 6",
            hook="Motivation comes and goes like the weather. Systems don't. Habits take ~66 days on average, and if-then plans help you follow through.",
            sources=["Lally, van Jaarsveld, Potts & Wardle (2010), 'How are habits formed', European Journal of Social Psychology (UCL)",
                     "Gollwitzer & Sheeran (2006), meta-analysis of implementation intentions (94 independent tests), Advances in Experimental Social Psychology",
                     "James Clear, 'Atomic Habits'"],
            tags=["motivation", "discipline", "habit formation", "66 days habit", "if then plans", "habit stacking"],
            pinned="Write your if-then plan below: 'If ____, then I will ____.' Bolt will cheer you on!"),
    7: dict(title="Your Future Self Needs You (Why 'Later' Feels Free) | Bolt vs Later Ep. 7",
            hook="Your brain treats future-you a bit like a stranger, so 'later' feels free. Three ways to make future-you real.",
            sources=["Ersner-Hershfield, Wimmer & Knutson (2009), neural self-continuity, Social Cognitive and Affective Neuroscience",
                     "Hershfield et al. (2011), age-progressed renderings and saving, Journal of Marketing Research",
                     "Suzy Welch, '10-10-10'"],
            tags=["future self", "temporal discounting", "delayed gratification", "10 10 10 rule", "self control"],
            pinned="What's one line from your letter to future you? Share it below!"),
    8: dict(title="Tired All the Time? Burnout & Why Rest Isn't Lazy | Bolt vs Later Ep. 8",
            hook="Sometimes procrastination isn't about willpower at all. Your battery is just empty. How to recharge for real.",
            sources=["World Health Organization (2019), burnout as an occupational phenomenon in ICD-11",
                     "Talker Research poll of 2,000 people on young adults' stress",
                     "Watson et al. (2015), AASM/SRS recommended sleep for adults",
                     "Francesco Cirillo, the Pomodoro Technique"],
            tags=["burnout", "always tired", "rest", "pomodoro technique", "sleep", "mental health", "work life balance"],
            pinned="What's your favorite REAL break (no screens)? Share it so others can try it! If you're struggling, please reach out to someone you trust."),
    9: dict(title="Stop Comparing Yourself to Others (Highlight Reel Trap) | Bolt vs Later Ep. 9",
            hook="You're comparing your behind-the-scenes to everyone's highlight reel. Change who you race, and the 1% rule does the rest.",
            sources=["Festinger, L. (1954), 'A theory of social comparison processes', Human Relations",
                     "The 1% rule: 1.01^365 = 37.8 (illustrative math)"],
            tags=["comparison", "stop comparing yourself", "social media", "self worth", "1 percent better", "confidence"],
            pinned="Share ONE way you're better than you were a year ago. Small wins count!"),
    10: dict(title="You Failed. Now What? The Never-Miss-Twice Rule | Bolt vs Later Ep. 10",
             hook="Broke your streak? One slip barely matters. Never miss twice, forgive yourself, and restart with the tiniest version.",
             sources=["Lally et al. (2010), habit formation and missed opportunities, European Journal of Social Psychology",
                      "Wohl, Pychyl & Bennett (2010), self-forgiveness and procrastination",
                      "James Clear, 'Atomic Habits' (never miss twice)"],
             tags=["failure", "never miss twice", "how to restart", "all or nothing thinking", "resilience", "streak"],
             pinned="Which habit are you restarting today? Tiny version counts. Comment it and make it official!"),
}

SCENE_LABEL = {"title": "Intro", "struggle": "The struggle", "later": "Meet Lord Later", "talk": "The science",
               "compare": "The trap", "stat": "By the numbers", "win": "Victory!", "list": "Recap", "outro": "Your mission"}


def ts(t):
    t = int(t)
    return f"{t // 60}:{t % 60:02d}"


def chapters(ep):
    """Story-arc chapters (YouTube needs >= 3 chapters, each >= 10s, first at 0:00)."""
    beats = ep["beats"]

    def first(pred):
        for i, b in enumerate(beats):
            if pred(i, b):
                return b["start"]
        return None
    # the fight chapter starts where Lord Later taunts Bolt right before the first weapon
    first_later = next(i for i, b in enumerate(beats) if b["scene"] == "later")
    fi = next(i for i, b in enumerate(beats) if b["scene"] == "fight")
    j = fi
    while j - 1 > first_later + 1 and beats[j - 1]["scene"] == "later":
        j -= 1
    fight_start = beats[j]["start"]
    marks = [
        (first(lambda i, b: b["scene"] == "struggle"), "The struggle"),
        (first(lambda i, b: b["scene"] == "later"), "Meet Lord Later"),
        (first(lambda i, b: b["scene"] in ("talk", "stat", "compare") and i > 2), "The science"),
        (fight_start, "Bolt fights back: 3 weapons"),
        (first(lambda i, b: b["scene"] == "win"), "Victory!"),
        (first(lambda i, b: b["scene"] == "list"), "Recap"),
        (first(lambda i, b: b["scene"] == "outro"), "Your mission"),
    ]
    out = [(0.0, "Intro")]
    for (t, lab) in sorted([m for m in marks if m[0] is not None]):
        if t - out[-1][0] >= 10:
            out.append((t, lab))
    return out


def description(n, ep, meta, chs, total):
    lines = [meta["hook"], "",
             f"Meet Bolt, a tiny hero with a lightning bolt on their head, and Lord Later, the sleepy purple cloud king of putting things off. In every episode of {CHANNEL}, Bolt fights procrastination with real psychology and small, doable weapons.",
             "", "⏱️ CHAPTERS"]
    lines += [f"{ts(t)} {lab}" for (t, lab) in chs]
    lines += ["", "📚 SOURCES & FURTHER READING"] + [f"• {s}" for s in meta["sources"]]
    lines += ["", f"🎯 YOUR MISSION: {[b for b in ep['beats'] if b['scene'] == 'outro'][0]['mission']}",
              "", f"Subscribe for a new Bolt vs Later episode every week. {TAGLINE}",
              "", "This video is for education and motivation, not medical or mental-health advice. If you're struggling, please talk to a doctor or someone you trust.",
              "", "#procrastination #motivation #productivity #selfimprovement #boltvslater"]
    return "\n".join(lines)


def make_all():
    allm = []
    md = [f"# {CHANNEL}: YouTube upload kit", "", f"*{TAGLINE}*", ""]
    for n in range(1, 11):
        ep = copy.deepcopy(importlib.import_module(f"episodes.ep{n:02d}").EP)
        total, _, _, _ = build_timeline(ep)
        meta = META[n]
        chs = chapters(ep)
        desc = description(n, ep, meta, chs, total)
        tags = meta["tags"] + COMMON_TAGS
        while len(",".join(tags)) > 480:
            tags.pop()
        rec = dict(episode=n, file=f"videos/ep{n:02d}.mp4", thumbnail=f"thumbnails/ep{n:02d}_thumbnail.jpg",
                   duration=ts(total), title=meta["title"], description=desc, tags=tags, pinned_comment=meta["pinned"])
        allm.append(rec)
        with open(os.path.join(OUT, "descriptions", f"ep{n:02d}_description.txt"), "w") as f:
            f.write(f"TITLE:\n{meta['title']}\n\nDESCRIPTION:\n{desc}\n\nTAGS:\n{', '.join(tags)}\n\nPINNED COMMENT:\n{meta['pinned']}\n")
        md += [f"## Episode {n}: {meta['title']}", "",
               f"- **Video:** `output/videos/ep{n:02d}.mp4` ({ts(total)})",
               f"- **Thumbnail:** `output/thumbnails/ep{n:02d}_thumbnail.jpg`",
               f"- **Tags:** {', '.join(tags)}", f"- **Pinned comment:** {meta['pinned']}", "",
               "```", desc, "```", ""]
    with open(os.path.join(OUT, "youtube_metadata.json"), "w") as f:
        json.dump(allm, f, indent=2, ensure_ascii=False)
    with open(os.path.join(OUT, "UPLOAD_KIT.md"), "w") as f:
        f.write("\n".join(md))
    return allm
