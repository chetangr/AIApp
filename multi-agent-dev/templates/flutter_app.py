import os
import re
import subprocess
import shutil
from typing import Dict, Any, List

# Import required utilities
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import log_agent_activity

def create_flutter_app(task, app_name, project_dir):
    """
    Create a real Flutter app based on the task requirements
    
    This function will:
    1. Run 'flutter create' to generate a real Flutter project
    2. Modify the generated project based on task requirements
    3. Add custom code, models, and screens based on app type
    """
    log_agent_activity("developer", f"Creating Flutter app: {app_name}")
    
    # Check if Flutter is installed
    try:
        # Check flutter version
        subprocess.run(["flutter", "--version"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        log_agent_activity("error_handling", "Flutter SDK not found. Please install Flutter and add it to your PATH.")
        return False
    
    # Extract app features from task
    app_features = extract_app_features(task)
    
    # Create a clean app_name for Flutter (lowercase, underscores for spaces)
    safe_app_name = app_name.lower().replace(" ", "_").replace("-", "_")
    
    # Create the Flutter project using flutter create command
    try:
        log_agent_activity("developer", f"Running 'flutter create {safe_app_name}'")
        
        # If the directory already exists, create in a temp location and then copy contents
        if os.path.exists(project_dir):
            temp_dir = f"{project_dir}_temp"
            os.makedirs(temp_dir, exist_ok=True)
            
            # Run flutter create in the temp directory
            subprocess.run(
                ["flutter", "create", safe_app_name], 
                check=True, 
                cwd=os.path.dirname(temp_dir)
            )
            
            # Copy the files from temp to the actual project directory
            temp_project_dir = os.path.join(os.path.dirname(temp_dir), safe_app_name)
            for item in os.listdir(temp_project_dir):
                source = os.path.join(temp_project_dir, item)
                dest = os.path.join(project_dir, item)
                if os.path.isdir(source):
                    if not os.path.exists(dest):
                        shutil.copytree(source, dest)
                else:
                    shutil.copy2(source, dest)
            
            # Clean up the temp directory
            shutil.rmtree(temp_dir)
            if os.path.exists(temp_project_dir):
                shutil.rmtree(temp_project_dir)
        else:
            # Create the project directory
            os.makedirs(os.path.dirname(project_dir), exist_ok=True)
            
            # Run flutter create directly
            subprocess.run(
                ["flutter", "create", safe_app_name], 
                check=True, 
                cwd=os.path.dirname(project_dir)
            )
    except subprocess.CalledProcessError as e:
        log_agent_activity("error_handling", f"Error creating Flutter project: {str(e)}")
        return False
    
    # Now customize the generated project based on app features
    try:
        customize_flutter_project(project_dir, app_name, task, app_features)
        return True
    except Exception as e:
        log_agent_activity("error_handling", f"Error customizing Flutter project: {str(e)}")
        return False

def extract_app_features(task):
    """Extract app features from the task description"""
    title = task.get("title", "").lower()
    description = task.get("description", "").lower()
    content = title + " " + description
    
    app_features = {
        "app_type": "generic",
        "features": []
    }
    
    # Learning app detection
    if any(word in content for word in ["learn", "learning", "education", "study", "course", "skill", "upskill"]):
        app_features["app_type"] = "learning"
        if "track" in content or "progress" in content:
            app_features["features"].append("progress_tracking")
        if "flash" in content or "card" in content:
            app_features["features"].append("flashcards")
        if "quiz" in content or "test" in content:
            app_features["features"].append("quizzes")
        if "notif" in content:
            app_features["features"].append("notifications")
        if "interview" in content:
            app_features["features"].append("practice_interviews")
    
    # Pet diary detection
    elif any(word in content for word in ["pet", "animal", "dog", "cat", "diary"]):
        app_features["app_type"] = "pet_diary"
        app_features["features"] = ["activity_tracking", "reminders", "photo_gallery"]
    
    # E-commerce detection
    elif any(word in content for word in ["shop", "store", "ecommerce", "product", "cart"]):
        app_features["app_type"] = "ecommerce"
        app_features["features"] = ["product_browsing", "shopping_cart", "checkout"]
    
    # Social media detection
    elif any(word in content for word in ["social", "friend", "network", "post", "share"]):
        app_features["app_type"] = "social"
        app_features["features"] = ["posts", "profiles", "comments"]
    
    # Ensure we have at least some features
    if not app_features["features"]:
        app_features["features"] = ["basic_functionality", "user_profiles", "settings"]
    
    return app_features

def customize_flutter_project(project_dir, app_name, task, app_features):
    """Customize the generated Flutter project based on app features"""
    log_agent_activity("developer", f"Customizing Flutter project with features: {app_features['features']}")
    
    # Get display name for the app
    display_name = app_name.replace('_', ' ').title()
    
    # Update pubspec.yaml with additional dependencies
    pubspec_path = os.path.join(project_dir, "pubspec.yaml")
    if os.path.exists(pubspec_path):
        with open(pubspec_path, 'r') as f:
            pubspec_content = f.read()
        
        # Add additional dependencies based on features
        dependencies = []
        if "database" in app_features["features"] or app_features["app_type"] in ["learning", "pet_diary"]:
            dependencies.append("  sqflite: ^2.3.0")
            dependencies.append("  path_provider: ^2.1.1")
        
        if "notifications" in app_features["features"]:
            dependencies.append("  flutter_local_notifications: ^16.2.0")
        
        if "flashcards" in app_features["features"]:
            dependencies.append("  flip_card: ^0.7.0")
            
        if any(f in app_features["features"] for f in ["photo_gallery", "images", "camera"]):
            dependencies.append("  image_picker: ^1.0.4")
            
        if "http" in app_features["features"] or app_features["app_type"] in ["ecommerce", "social"]:
            dependencies.append("  http: ^1.1.0")
            
        # Add provider for state management
        dependencies.append("  provider: ^6.0.5")
        
        # Update pubspec.yaml with new dependencies
        if dependencies:
            # Find the dependencies section
            deps_section = "dependencies:\n  flutter:\n    sdk: flutter"
            updated_deps = deps_section + "\n" + "\n".join(dependencies)
            pubspec_content = pubspec_content.replace(deps_section, updated_deps)
            
            # Update the app name and description
            pubspec_content = re.sub(r'name: \w+', f'name: {app_name.lower()}', pubspec_content)
            pubspec_content = re.sub(r'description: .*', f'description: {task.get("description", "A Flutter application")}', pubspec_content)
            
            # Write the updated pubspec
            with open(pubspec_path, 'w') as f:
                f.write(pubspec_content)
    
    # Update app title in AndroidManifest.xml
    android_manifest_path = os.path.join(project_dir, "android", "app", "src", "main", "AndroidManifest.xml")
    if os.path.exists(android_manifest_path):
        with open(android_manifest_path, 'r') as f:
            manifest_content = f.read()
        
        # Update app name
        manifest_content = re.sub(r'android:label="[^"]*"', f'android:label="{display_name}"', manifest_content)
        
        with open(android_manifest_path, 'w') as f:
            f.write(manifest_content)
    
    # Create app models based on app type
    models_dir = os.path.join(project_dir, "lib", "models")
    os.makedirs(models_dir, exist_ok=True)
    
    # Create models based on app type
    if app_features["app_type"] == "learning":
        create_learning_app_models(models_dir)
    elif app_features["app_type"] == "pet_diary":
        create_pet_diary_models(models_dir)
    elif app_features["app_type"] == "ecommerce":
        create_ecommerce_models(models_dir)
    elif app_features["app_type"] == "social":
        create_social_models(models_dir)
    
    # Create screens directory
    screens_dir = os.path.join(project_dir, "lib", "screens")
    os.makedirs(screens_dir, exist_ok=True)
    
    # Create services directory
    services_dir = os.path.join(project_dir, "lib", "services")
    os.makedirs(services_dir, exist_ok=True)
    
    # Create a database helper if needed
    if "database" in app_features["features"] or app_features["app_type"] in ["learning", "pet_diary"]:
        create_database_helper(services_dir, app_features["app_type"])
    
    # Update the main.dart file
    update_main_dart(project_dir, display_name, app_features)
    
    # Run flutter pub get to install dependencies
    try:
        log_agent_activity("developer", "Running 'flutter pub get' to install dependencies")
        subprocess.run(
            ["flutter", "pub", "get"],
            check=True,
            cwd=project_dir
        )
    except subprocess.CalledProcessError as e:
        log_agent_activity("error_handling", f"Error installing dependencies: {str(e)}")

def create_learning_app_models(models_dir):
    """Create models for a learning app"""
    # Course model
    course_model_path = os.path.join(models_dir, "course.dart")
    course_model_content = """class Course {
  final int id;
  final String title;
  final String description;
  final String category;
  final int difficulty;
  final String imageUrl;
  final String createdAt;

  Course({
    required this.id,
    required this.title,
    required this.description,
    required this.category,
    required this.difficulty,
    this.imageUrl = '',
    required this.createdAt,
  });

  Map<String, dynamic> toMap() {
    return {
      'id': id,
      'title': title,
      'description': description,
      'category': category,
      'difficulty': difficulty,
      'imageUrl': imageUrl,
      'createdAt': createdAt,
    };
  }

  factory Course.fromMap(Map<String, dynamic> map) {
    return Course(
      id: map['id'],
      title: map['title'],
      description: map['description'],
      category: map['category'],
      difficulty: map['difficulty'],
      imageUrl: map['imageUrl'] ?? '',
      createdAt: map['createdAt'],
    );
  }
}
"""
    with open(course_model_path, "w") as f:
        f.write(course_model_content)
    
    # Flashcard model
    flashcard_model_path = os.path.join(models_dir, "flashcard.dart")
    flashcard_model_content = """class Flashcard {
  final int id;
  final int courseId;
  final String question;
  final String answer;
  final int difficulty;

  Flashcard({
    required this.id,
    required this.courseId,
    required this.question,
    required this.answer,
    required this.difficulty,
  });

  Map<String, dynamic> toMap() {
    return {
      'id': id,
      'courseId': courseId,
      'question': question,
      'answer': answer,
      'difficulty': difficulty,
    };
  }

  factory Flashcard.fromMap(Map<String, dynamic> map) {
    return Flashcard(
      id: map['id'],
      courseId: map['courseId'],
      question: map['question'],
      answer: map['answer'],
      difficulty: map['difficulty'],
    );
  }
}
"""
    with open(flashcard_model_path, "w") as f:
        f.write(flashcard_model_content)
    
    # Quiz model
    quiz_model_path = os.path.join(models_dir, "quiz.dart")
    quiz_model_content = """class Quiz {
  final int id;
  final int courseId;
  final String title;
  final List<Question> questions;

  Quiz({
    required this.id,
    required this.courseId,
    required this.title,
    required this.questions,
  });

  Map<String, dynamic> toMap() {
    return {
      'id': id,
      'courseId': courseId,
      'title': title,
    };
  }

  factory Quiz.fromMap(Map<String, dynamic> map) {
    return Quiz(
      id: map['id'],
      courseId: map['courseId'],
      title: map['title'],
      questions: [],
    );
  }
}

class Question {
  final int id;
  final int quizId;
  final String questionText;
  final List<Option> options;
  final int correctOptionId;

  Question({
    required this.id,
    required this.quizId,
    required this.questionText,
    required this.options,
    required this.correctOptionId,
  });

  Map<String, dynamic> toMap() {
    return {
      'id': id,
      'quizId': quizId,
      'questionText': questionText,
      'correctOptionId': correctOptionId,
    };
  }

  factory Question.fromMap(Map<String, dynamic> map) {
    return Question(
      id: map['id'],
      quizId: map['quizId'],
      questionText: map['questionText'],
      options: [],
      correctOptionId: map['correctOptionId'],
    );
  }
}

class Option {
  final int id;
  final int questionId;
  final String optionText;

  Option({
    required this.id,
    required this.questionId,
    required this.optionText,
  });

  Map<String, dynamic> toMap() {
    return {
      'id': id,
      'questionId': questionId,
      'optionText': optionText,
    };
  }

  factory Option.fromMap(Map<String, dynamic> map) {
    return Option(
      id: map['id'],
      questionId: map['questionId'],
      optionText: map['optionText'],
    );
  }
}
"""
    with open(quiz_model_path, "w") as f:
        f.write(quiz_model_content)

def create_pet_diary_models(models_dir):
    """Create models for a pet diary app"""
    # Diary entry model
    diary_entry_path = os.path.join(models_dir, "diary_entry.dart")
    diary_entry_content = """class DiaryEntry {
  final int id;
  final String title;
  final String description;
  final String activity;
  final String date;
  final String? imagePath;

  DiaryEntry({
    required this.id,
    required this.title,
    required this.description,
    required this.activity,
    required this.date,
    this.imagePath,
  });

  Map<String, dynamic> toMap() {
    return {
      'id': id,
      'title': title,
      'description': description,
      'activity': activity,
      'date': date,
      'imagePath': imagePath,
    };
  }

  factory DiaryEntry.fromMap(Map<String, dynamic> map) {
    return DiaryEntry(
      id: map['id'],
      title: map['title'],
      description: map['description'],
      activity: map['activity'],
      date: map['date'],
      imagePath: map['imagePath'],
    );
  }
}
"""
    with open(diary_entry_path, "w") as f:
        f.write(diary_entry_content)
    
    # Pet model
    pet_model_path = os.path.join(models_dir, "pet.dart")
    pet_model_content = """class Pet {
  final int id;
  final String name;
  final String type;
  final String breed;
  final String dateOfBirth;
  final String? imagePath;

  Pet({
    required this.id,
    required this.name,
    required this.type,
    required this.breed,
    required this.dateOfBirth,
    this.imagePath,
  });

  Map<String, dynamic> toMap() {
    return {
      'id': id,
      'name': name,
      'type': type,
      'breed': breed,
      'dateOfBirth': dateOfBirth,
      'imagePath': imagePath,
    };
  }

  factory Pet.fromMap(Map<String, dynamic> map) {
    return Pet(
      id: map['id'],
      name: map['name'],
      type: map['type'],
      breed: map['breed'],
      dateOfBirth: map['dateOfBirth'],
      imagePath: map['imagePath'],
    );
  }
}
"""
    with open(pet_model_path, "w") as f:
        f.write(pet_model_content)

def create_ecommerce_models(models_dir):
    """Create models for an e-commerce app"""
    # Product model
    product_model_path = os.path.join(models_dir, "product.dart")
    product_model_content = """class Product {
  final int id;
  final String name;
  final String description;
  final double price;
  final String category;
  final String imageUrl;
  final int stockQuantity;

  Product({
    required this.id,
    required this.name,
    required this.description,
    required this.price,
    required this.category,
    required this.imageUrl,
    required this.stockQuantity,
  });

  Map<String, dynamic> toMap() {
    return {
      'id': id,
      'name': name,
      'description': description,
      'price': price,
      'category': category,
      'imageUrl': imageUrl,
      'stockQuantity': stockQuantity,
    };
  }

  factory Product.fromMap(Map<String, dynamic> map) {
    return Product(
      id: map['id'],
      name: map['name'],
      description: map['description'],
      price: map['price'],
      category: map['category'],
      imageUrl: map['imageUrl'],
      stockQuantity: map['stockQuantity'],
    );
  }
}
"""
    with open(product_model_path, "w") as f:
        f.write(product_model_content)
    
    # Cart model
    cart_model_path = os.path.join(models_dir, "cart.dart")
    cart_model_content = """import 'product.dart';

class CartItem {
  final Product product;
  int quantity;

  CartItem({
    required this.product,
    this.quantity = 1,
  });

  double get total => product.price * quantity;
}

class Cart {
  List<CartItem> items = [];

  double get totalPrice =>
      items.fold(0, (total, item) => total + item.total);

  int get itemCount => items.length;

  void addItem(Product product, {int quantity = 1}) {
    final existingIndex = items.indexWhere((item) => item.product.id == product.id);
    
    if (existingIndex >= 0) {
      items[existingIndex].quantity += quantity;
    } else {
      items.add(CartItem(product: product, quantity: quantity));
    }
  }

  void removeItem(int productId) {
    items.removeWhere((item) => item.product.id == productId);
  }

  void updateQuantity(int productId, int quantity) {
    final index = items.indexWhere((item) => item.product.id == productId);
    if (index >= 0) {
      items[index].quantity = quantity;
    }
  }

  void clear() {
    items.clear();
  }
}
"""
    with open(cart_model_path, "w") as f:
        f.write(cart_model_content)

def create_social_models(models_dir):
    """Create models for a social media app"""
    # User model
    user_model_path = os.path.join(models_dir, "user.dart")
    user_model_content = """class User {
  final int id;
  final String username;
  final String email;
  final String? profileImageUrl;
  final String bio;
  final String joinDate;
  final List<int> followers;
  final List<int> following;

  User({
    required this.id,
    required this.username,
    required this.email,
    this.profileImageUrl,
    required this.bio,
    required this.joinDate,
    required this.followers,
    required this.following,
  });

  Map<String, dynamic> toMap() {
    return {
      'id': id,
      'username': username,
      'email': email,
      'profileImageUrl': profileImageUrl,
      'bio': bio,
      'joinDate': joinDate,
      'followers': followers,
      'following': following,
    };
  }

  factory User.fromMap(Map<String, dynamic> map) {
    return User(
      id: map['id'],
      username: map['username'],
      email: map['email'],
      profileImageUrl: map['profileImageUrl'],
      bio: map['bio'],
      joinDate: map['joinDate'],
      followers: List<int>.from(map['followers'] ?? []),
      following: List<int>.from(map['following'] ?? []),
    );
  }
}
"""
    with open(user_model_path, "w") as f:
        f.write(user_model_content)
    
    # Post model
    post_model_path = os.path.join(models_dir, "post.dart")
    post_model_content = """class Post {
  final int id;
  final int userId;
  final String content;
  final String? imageUrl;
  final String createdAt;
  final List<int> likes;
  final List<Comment> comments;

  Post({
    required this.id,
    required this.userId,
    required this.content,
    this.imageUrl,
    required this.createdAt,
    required this.likes,
    required this.comments,
  });

  Map<String, dynamic> toMap() {
    return {
      'id': id,
      'userId': userId,
      'content': content,
      'imageUrl': imageUrl,
      'createdAt': createdAt,
      'likes': likes,
    };
  }

  factory Post.fromMap(Map<String, dynamic> map) {
    return Post(
      id: map['id'],
      userId: map['userId'],
      content: map['content'],
      imageUrl: map['imageUrl'],
      createdAt: map['createdAt'],
      likes: List<int>.from(map['likes'] ?? []),
      comments: [],
    );
  }
}

class Comment {
  final int id;
  final int postId;
  final int userId;
  final String content;
  final String createdAt;

  Comment({
    required this.id,
    required this.postId,
    required this.userId,
    required this.content,
    required this.createdAt,
  });

  Map<String, dynamic> toMap() {
    return {
      'id': id,
      'postId': postId,
      'userId': userId,
      'content': content,
      'createdAt': createdAt,
    };
  }

  factory Comment.fromMap(Map<String, dynamic> map) {
    return Comment(
      id: map['id'],
      postId: map['postId'],
      userId: map['userId'],
      content: map['content'],
      createdAt: map['createdAt'],
    );
  }
}
"""
    with open(post_model_path, "w") as f:
        f.write(post_model_content)

def create_database_helper(services_dir, app_type):
    """Create a database helper based on app type"""
    db_helper_path = os.path.join(services_dir, "database_helper.dart")
    
    # Customize the database helper based on app type
    if app_type == "learning":
        db_helper_content = """import 'dart:async';
import 'package:sqflite/sqflite.dart';
import 'package:path/path.dart';
import '../models/course.dart';
import '../models/flashcard.dart';
import '../models/quiz.dart';

class DatabaseHelper {
  static final DatabaseHelper _instance = DatabaseHelper._internal();
  static Database? _database;

  factory DatabaseHelper() => _instance;

  DatabaseHelper._internal();

  Future<Database> get database async {
    if (_database != null) return _database!;
    _database = await _initDatabase();
    return _database!;
  }

  Future<Database> _initDatabase() async {
    String path = join(await getDatabasesPath(), 'learning_app.db');
    return await openDatabase(
      path,
      version: 1,
      onCreate: _createDb,
    );
  }

  Future<void> _createDb(Database db, int version) async {
    // Create courses table
    await db.execute('''
      CREATE TABLE courses(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        description TEXT,
        category TEXT,
        difficulty INTEGER,
        imageUrl TEXT,
        createdAt TEXT
      )
    ''');
    
    // Create flashcards table
    await db.execute('''
      CREATE TABLE flashcards(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        courseId INTEGER,
        question TEXT,
        answer TEXT,
        difficulty INTEGER,
        FOREIGN KEY (courseId) REFERENCES courses (id)
      )
    ''');
    
    // Create quizzes table
    await db.execute('''
      CREATE TABLE quizzes(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        courseId INTEGER,
        title TEXT,
        FOREIGN KEY (courseId) REFERENCES courses (id)
      )
    ''');
    
    // Create questions table
    await db.execute('''
      CREATE TABLE questions(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        quizId INTEGER,
        questionText TEXT,
        correctOptionId INTEGER,
        FOREIGN KEY (quizId) REFERENCES quizzes (id)
      )
    ''');
    
    // Create options table
    await db.execute('''
      CREATE TABLE options(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        questionId INTEGER,
        optionText TEXT,
        FOREIGN KEY (questionId) REFERENCES questions (id)
      )
    ''');
    
    // Insert some sample data
    await db.insert('courses', {
      'title': 'Flutter Basics',
      'description': 'Learn the basics of Flutter development',
      'category': 'Programming',
      'difficulty': 1,
      'imageUrl': '',
      'createdAt': DateTime.now().toIso8601String()
    });
    
    await db.insert('courses', {
      'title': 'Advanced Dart',
      'description': 'Master Dart programming language',
      'category': 'Programming',
      'difficulty': 3,
      'imageUrl': '',
      'createdAt': DateTime.now().toIso8601String()
    });
  }

  // Course methods
  Future<int> insertCourse(Course course) async {
    Database db = await database;
    return await db.insert('courses', course.toMap());
  }

  Future<List<Course>> getCourses() async {
    Database db = await database;
    final List<Map<String, dynamic>> maps = await db.query('courses');
    return List.generate(maps.length, (i) {
      return Course.fromMap(maps[i]);
    });
  }

  Future<Course?> getCourse(int id) async {
    Database db = await database;
    final List<Map<String, dynamic>> maps = await db.query(
      'courses',
      where: 'id = ?',
      whereArgs: [id],
    );
    if (maps.isNotEmpty) {
      return Course.fromMap(maps.first);
    }
    return null;
  }

  // Flashcard methods
  Future<int> insertFlashcard(Flashcard flashcard) async {
    Database db = await database;
    return await db.insert('flashcards', flashcard.toMap());
  }

  Future<List<Flashcard>> getFlashcardsByCourse(int courseId) async {
    Database db = await database;
    final List<Map<String, dynamic>> maps = await db.query(
      'flashcards',
      where: 'courseId = ?',
      whereArgs: [courseId],
    );
    return List.generate(maps.length, (i) {
      return Flashcard.fromMap(maps[i]);
    });
  }

  // Quiz methods
  Future<int> insertQuiz(Quiz quiz) async {
    Database db = await database;
    return await db.insert('quizzes', quiz.toMap());
  }

  Future<List<Quiz>> getQuizzesByCourse(int courseId) async {
    Database db = await database;
    final List<Map<String, dynamic>> maps = await db.query(
      'quizzes',
      where: 'courseId = ?',
      whereArgs: [courseId],
    );
    return List.generate(maps.length, (i) {
      return Quiz.fromMap(maps[i]);
    });
  }
}
"""
    elif app_type == "pet_diary":
        db_helper_content = """import 'dart:async';
import 'package:sqflite/sqflite.dart';
import 'package:path/path.dart';
import '../models/diary_entry.dart';
import '../models/pet.dart';

class DatabaseHelper {
  static final DatabaseHelper _instance = DatabaseHelper._internal();
  static Database? _database;

  factory DatabaseHelper() => _instance;

  DatabaseHelper._internal();

  Future<Database> get database async {
    if (_database != null) return _database!;
    _database = await _initDatabase();
    return _database!;
  }

  Future<Database> _initDatabase() async {
    String path = join(await getDatabasesPath(), 'pet_diary.db');
    return await openDatabase(
      path,
      version: 1,
      onCreate: _createDb,
    );
  }

  Future<void> _createDb(Database db, int version) async {
    // Create pets table
    await db.execute('''
      CREATE TABLE pets(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        type TEXT,
        breed TEXT,
        dateOfBirth TEXT,
        imagePath TEXT
      )
    ''');
    
    // Create diary entries table
    await db.execute('''
      CREATE TABLE diary_entries(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        description TEXT,
        activity TEXT,
        date TEXT,
        imagePath TEXT
      )
    ''');
    
    // Insert some sample data
    await db.insert('pets', {
      'name': 'Buddy',
      'type': 'Dog',
      'breed': 'Golden Retriever',
      'dateOfBirth': '2020-01-15',
      'imagePath': ''
    });
  }

  // Pet methods
  Future<int> insertPet(Pet pet) async {
    Database db = await database;
    return await db.insert('pets', pet.toMap());
  }

  Future<List<Pet>> getPets() async {
    Database db = await database;
    final List<Map<String, dynamic>> maps = await db.query('pets');
    return List.generate(maps.length, (i) {
      return Pet.fromMap(maps[i]);
    });
  }

  Future<Pet?> getPet(int id) async {
    Database db = await database;
    final List<Map<String, dynamic>> maps = await db.query(
      'pets',
      where: 'id = ?',
      whereArgs: [id],
    );
    if (maps.isNotEmpty) {
      return Pet.fromMap(maps.first);
    }
    return null;
  }

  // Diary entry methods
  Future<int> insertEntry(DiaryEntry entry) async {
    Database db = await database;
    return await db.insert('diary_entries', entry.toMap());
  }

  Future<List<DiaryEntry>> getEntries() async {
    Database db = await database;
    final List<Map<String, dynamic>> maps = await db.query(
      'diary_entries',
      orderBy: 'date DESC'
    );
    return List.generate(maps.length, (i) {
      return DiaryEntry.fromMap(maps[i]);
    });
  }

  Future<DiaryEntry?> getEntry(int id) async {
    Database db = await database;
    final List<Map<String, dynamic>> maps = await db.query(
      'diary_entries',
      where: 'id = ?',
      whereArgs: [id],
    );
    if (maps.isNotEmpty) {
      return DiaryEntry.fromMap(maps.first);
    }
    return null;
  }

  Future<int> updateEntry(DiaryEntry entry) async {
    Database db = await database;
    return await db.update(
      'diary_entries',
      entry.toMap(),
      where: 'id = ?',
      whereArgs: [entry.id],
    );
  }

  Future<int> deleteEntry(int id) async {
    Database db = await database;
    return await db.delete(
      'diary_entries',
      where: 'id = ?',
      whereArgs: [id],
    );
  }
}
"""
    else:
        # Generic database helper
        db_helper_content = """import 'dart:async';
import 'package:sqflite/sqflite.dart';
import 'package:path/path.dart';

class DatabaseHelper {
  static final DatabaseHelper _instance = DatabaseHelper._internal();
  static Database? _database;

  factory DatabaseHelper() => _instance;

  DatabaseHelper._internal();

  Future<Database> get database async {
    if (_database != null) return _database!;
    _database = await _initDatabase();
    return _database!;
  }

  Future<Database> _initDatabase() async {
    String path = join(await getDatabasesPath(), 'app_database.db');
    return await openDatabase(
      path,
      version: 1,
      onCreate: _createDb,
    );
  }

  Future<void> _createDb(Database db, int version) async {
    // Create tables here
    await db.execute('''
      CREATE TABLE items(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        description TEXT,
        date TEXT
      )
    ''');
  }

  // Generic CRUD operations
  Future<int> insert(String table, Map<String, dynamic> data) async {
    Database db = await database;
    return await db.insert(table, data);
  }

  Future<List<Map<String, dynamic>>> query(String table, {
    String? where,
    List<dynamic>? whereArgs,
    String? orderBy,
  }) async {
    Database db = await database;
    return await db.query(
      table,
      where: where,
      whereArgs: whereArgs,
      orderBy: orderBy,
    );
  }

  Future<int> update(String table, Map<String, dynamic> data, {
    required String where,
    required List<dynamic> whereArgs,
  }) async {
    Database db = await database;
    return await db.update(
      table,
      data,
      where: where,
      whereArgs: whereArgs,
    );
  }

  Future<int> delete(String table, {
    required String where,
    required List<dynamic> whereArgs,
  }) async {
    Database db = await database;
    return await db.delete(
      table,
      where: where,
      whereArgs: whereArgs,
    );
  }
}
"""
    
    with open(db_helper_path, "w") as f:
        f.write(db_helper_content)

def update_main_dart(project_dir, display_name, app_features):
    """Update the main.dart file with customized app code"""
    main_dart_path = os.path.join(project_dir, "lib", "main.dart")
    
    # Create custom main.dart based on app type
    if app_features["app_type"] == "learning":
        main_content = f"""import 'package:flutter/material.dart';
import 'models/course.dart';
import 'services/database_helper.dart';

void main() {{
  runApp(const MyApp());
}}

class MyApp extends StatelessWidget {{
  const MyApp({{super.key}});

  @override
  Widget build(BuildContext context) {{
    return MaterialApp(
      title: '{display_name}',
      theme: ThemeData(
        primarySwatch: Colors.blue,
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.blue),
        useMaterial3: true,
      ),
      home: const HomeScreen(),
    );
  }}
}}

class HomeScreen extends StatefulWidget {{
  const HomeScreen({{super.key}});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}}

class _HomeScreenState extends State<HomeScreen> {{
  final DatabaseHelper _dbHelper = DatabaseHelper();
  List<Course> _courses = [];
  bool _isLoading = true;

  @override
  void initState() {{
    super.initState();
    _loadCourses();
  }}

  Future<void> _loadCourses() async {{
    try {{
      final courses = await _dbHelper.getCourses();
      setState(() {{
        _courses = courses;
        _isLoading = false;
      }});
    }} catch (e) {{
      setState(() {{
        _isLoading = false;
      }});
      if (mounted) {{
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Error loading courses')),
        );
      }}
    }}
  }}

  @override
  Widget build(BuildContext context) {{
    return Scaffold(
      appBar: AppBar(
        title: Text('{display_name}'),
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _courses.isEmpty
              ? const Center(child: Text('No courses available'))
              : ListView.builder(
                  itemCount: _courses.length,
                  itemBuilder: (context, index) {{
                    final course = _courses[index];
                    return Card(
                      margin: const EdgeInsets.all(8.0),
                      child: ListTile(
                        title: Text(course.title),
                        subtitle: Text(course.description),
                        trailing: const Icon(Icons.arrow_forward_ios),
                        onTap: () {{
                          // Navigate to course detail screen
                        }},
                      ),
                    );
                  }},
                ),
      floatingActionButton: FloatingActionButton(
        onPressed: () {{
          // Add new course
        }},
        tooltip: 'Add Course',
        child: const Icon(Icons.add),
      ),
    );
  }}
}}
"""
    elif app_features["app_type"] == "pet_diary":
        main_content = f"""import 'package:flutter/material.dart';
import 'models/diary_entry.dart';
import 'services/database_helper.dart';

void main() {{
  runApp(const MyApp());
}}

class MyApp extends StatelessWidget {{
  const MyApp({{super.key}});

  @override
  Widget build(BuildContext context) {{
    return MaterialApp(
      title: '{display_name}',
      theme: ThemeData(
        primarySwatch: Colors.blue,
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.blue),
        useMaterial3: true,
      ),
      home: const HomeScreen(),
    );
  }}
}}

class HomeScreen extends StatefulWidget {{
  const HomeScreen({{super.key}});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}}

class _HomeScreenState extends State<HomeScreen> {{
  final DatabaseHelper _dbHelper = DatabaseHelper();
  List<DiaryEntry> _entries = [];
  bool _isLoading = true;

  @override
  void initState() {{
    super.initState();
    _loadEntries();
  }}

  Future<void> _loadEntries() async {{
    try {{
      final entries = await _dbHelper.getEntries();
      setState(() {{
        _entries = entries;
        _isLoading = false;
      }});
    }} catch (e) {{
      setState(() {{
        _isLoading = false;
      }});
      if (mounted) {{
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Error loading entries')),
        );
      }}
    }}
  }}

  @override
  Widget build(BuildContext context) {{
    return Scaffold(
      appBar: AppBar(
        title: Text('{display_name}'),
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _entries.isEmpty
              ? const Center(child: Text('No entries yet. Add your first one!'))
              : ListView.builder(
                  itemCount: _entries.length,
                  itemBuilder: (context, index) {{
                    final entry = _entries[index];
                    return Card(
                      margin: const EdgeInsets.all(8.0),
                      child: ListTile(
                        title: Text(entry.title),
                        subtitle: Text('${{entry.activity}} • ${{entry.date}}'),
                        trailing: const Icon(Icons.arrow_forward_ios),
                        onTap: () {{
                          // Navigate to entry details
                        }},
                      ),
                    );
                  }},
                ),
      floatingActionButton: FloatingActionButton(
        onPressed: () {{
          // Add new entry
        }},
        tooltip: 'Add Entry',
        child: const Icon(Icons.add),
      ),
    );
  }}
}}
"""
    else:
        # Generic main.dart for other app types
        main_content = f"""import 'package:flutter/material.dart';

void main() {{
  runApp(const MyApp());
}}

class MyApp extends StatelessWidget {{
  const MyApp({{super.key}});

  @override
  Widget build(BuildContext context) {{
    return MaterialApp(
      title: '{display_name}',
      theme: ThemeData(
        primarySwatch: Colors.blue,
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.blue),
        useMaterial3: true,
      ),
      home: const HomeScreen(),
    );
  }}
}}

class HomeScreen extends StatefulWidget {{
  const HomeScreen({{super.key}});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}}

class _HomeScreenState extends State<HomeScreen> {{
  final List<String> _features = {app_features["features"]};

  @override
  Widget build(BuildContext context) {{
    return Scaffold(
      appBar: AppBar(
        title: Text('{display_name}'),
      ),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: <Widget>[
            Text(
              'Welcome to {display_name}',
              style: Theme.of(context).textTheme.headlineMedium,
            ),
            const SizedBox(height: 20),
            const Text('Your new app is ready!'),
            const SizedBox(height: 40),
            Text('Features included:'),
            const SizedBox(height: 10),
            ...{app_features["features"]}.map((feature) => 
              Padding(
                padding: const EdgeInsets.all(4.0),
                child: Text('• ${{feature.replaceAll('_', ' ').toUpperCase()}}'),
              )
            ).toList(),
          ],
        ),
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () {{
          // Add action here
        }},
        tooltip: 'Action',
        child: const Icon(Icons.add),
      ),
    );
  }}
}}
"""
    
    with open(main_dart_path, "w") as f:
        f.write(main_content)