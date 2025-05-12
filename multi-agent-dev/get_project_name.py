def get_project_name_from_requirements(requirements):
    """Extract a project name from the requirements"""
    import re
    
    # Try to get a meaningful name from the requirements
    words = requirements.lower().split()
    project_words = []

    # First, look for direct mentions of project name
    direct_patterns = [
        r'create (?:an?|the) ([\w\s]+?) (?:app|application|system|platform)',
        r'develop (?:an?|the) ([\w\s]+?) (?:app|application|system|platform)',
        r'build (?:an?|the) ([\w\s]+?) (?:app|application|system|platform)',
        r'design (?:an?|the) ([\w\s]+?) (?:for|that|which|to)',
        r'implement (?:an?|the) ([\w\s]+?) (?:for|that|which|to)',
        r'app called ([\w\s]+?)[.,]',
        r'application called ([\w\s]+?)[.,]',
        r'system called ([\w\s]+?)[.,]',
        r'platform called ([\w\s]+?)[.,]'
    ]
    
    for pattern in direct_patterns:
        matches = re.search(pattern, requirements.lower())
        if matches and matches.group(1):
            candidate = matches.group(1).strip()
            if len(candidate.split()) <= 4 and len(candidate) > 3:
                project_words = candidate.split()
                break
    
    # Look for key phrases like "app for", "application for", "app to" if no direct name found
    phrases = ["app for", "application for", "app to", "system for", "platform for"]
    if not project_words:
        for phrase in phrases:
            if phrase in requirements.lower():
                # Extract what comes after the phrase, up to the next period or comma
                index = requirements.lower().find(phrase) + len(phrase)
                end_index = min(
                    [requirements.find(c, index) for c in ['.', ',', '\n'] if requirements.find(c, index) > 0] or [len(requirements)]
                )
                extracted = requirements[index:end_index].strip()
                
                # Use the first few words (2-3) after the phrase
                project_words = extracted.split()[:3]
                break

    # If no phrase was found, try to use key nouns
    if not project_words:
        nouns = ["diary", "tracker", "manager", "journal", "planner", "organizer", "app", "application", 
                "system", "calculator", "game", "messenger", "editor", "viewer", "browser", "platform", "dashboard"]
        for word in words:
            if word in nouns and len(project_words) < 3:
                project_words.append(word)

    # If we found some words, create a name
    if project_words:
        # Add subject if we can find it
        subjects = ["pet", "health", "fitness", "finance", "food", "recipe", "movie", "book", "task", 
                   "project", "weather", "music", "photo", "video", "chat", "social", "shopping", "travel", 
                   "note", "budget", "productivity", "education", "medical", "inventory", "employee"]
        for subject in subjects:
            if subject in words and subject not in ' '.join(project_words):
                project_words.insert(0, subject)
                break

        # Join words and clean up
        project_name = "_".join(project_words)
        project_name = re.sub(r'[^\w\s]', '', project_name)
        project_name = re.sub(r'_+', '_', project_name)  # Remove duplicate underscores
        return project_name

    # Extract first meaningful sentence if all else fails
    if len(requirements) > 10:
        first_sentence = requirements.split('.')[0].strip()
        words = first_sentence.split()
        if len(words) > 3:
            meaningful_words = [w for w in words[:4] if len(w) > 3 and w.lower() not in ['create', 'build', 'develop', 'design', 'implement', 'the', 'and', 'for']]
            if meaningful_words:
                return "_".join(meaningful_words).lower()

    # Default fallback
    return "my_project"