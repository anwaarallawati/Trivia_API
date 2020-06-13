import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random
# from sqlalchemy import  or_ #,exc

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10


def paginate_questions(request, selection):
    page = request.args.get('page', 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE

    questions = [question.format() for question in selection]
    current_questions = questions[start:end]

    return current_questions


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)
    db = SQLAlchemy(app)
    CORS(app)

    '''
    @TODO: Set up CORS. Allow '*' for origins. Delete the sample route after completing the TODOs
    '''

    '''
    @TODO-DONE: Use the after_request decorator to set Access-Control-Allow
    '''

    @app.after_request
    def after_request(response):
        response.headers.add(
            'Access-Control-Allow-Headers',
            'Content-Type,Authorization,true')
        response.headers.add(
            'Access-Control-Allow-Methods',
            'GET,PUT,POST,DELETE,OPTIONS')
        return response

    '''
    @TODO-DONE:
    Create an endpoint to handle GET requests
    for all available categories.
    '''
    @app.route('/categories')
    def get_categories():
        categories = Category.query.order_by(Category.id).all()
        category_names = {}
        # categories = [category.format() for category in selection]
        for category in categories:
            category_names[str(category.id)] = category.type

        return jsonify({
            'success': True,
            'categories': category_names
        })

    '''
    @TODO-DONE:
    Create an endpoint to handle GET requests for questions,
    including pagination (every 10 questions).
    This endpoint should return a list of questions,
    number of total questions, current category, categories.

    TEST: At this point, when you start the application
    you should see questions and categories generated,
    ten questions per page and pagination at the bottom of the screen for three pages.
    Clicking on the page numbers should update the questions.
    '''

    @app.route('/questions', methods=['GET'])
    def get_questions():
        selection = Question.query.order_by(Question.category).all()
        current_questions = paginate_questions(request, selection)
        categories = Category.query.order_by(Category.id).all()
        formatted_categories = [category.format() for category in categories]
        category_names = {}

        for category in categories:
            category_names[str(category.id)] = category.type

        if len(current_questions) == 0:
            abort(404)

        return jsonify({
            'success': True,
            'questions': current_questions,
            'total_questions': len(Question.query.all()),
            'categories': category_names
        })
    '''
    @TODO-DONE:
    Create an endpoint to DELETE question using a question ID.

    TEST: When you click the trash icon next to a question, the question will be removed.
    This removal will persist in the database and when you refresh the page.
    '''

    @app.route('/questions/<int:question_id>', methods=['DELETE'])
    def delete_question(question_id):

        try:
            question = Question.query.filter(
                Question.id == question_id).one_or_none()
            question.delete()
            questions_count = Question.query.count()

        except BaseException:
            db.session.rollback()

        finally:
            db.session.close()

        if question is None:
            abort(422)

        return jsonify({
            'success': True,
            'deleted_question_id': question_id,
            'total_questions': questions_count
        })

    '''
    @TODO-DONE:
    Create an endpoint to POST a new question,
    which will require the question and answer text,
    category, and difficulty score.

    TEST: When you submit a question on the "Add" tab,
    the form will clear and the question will appear at the end of the last page
    of the questions list in the "List" tab.
    '''

    @app.route('/questions', methods=['POST'])
    def create_question():

        body = request.get_json()

        question = body.get('question', None)
        answer = body.get('answer', None)
        category = body.get('category', None)
        difficulty = body.get('difficulty', None)

        try:
            question = Question(
                question=question,
                answer=answer,
                category=category,
                difficulty=difficulty)
            question.insert()
        except BaseException:
            db.session.rollback()
            abort(422)
        finally:
            db.session.close()

        if not question or not answer or not category or not difficulty:
            abort(422)
            return jsonify({
                'success': False
            })

        return jsonify({
            'success': True,
            'question': question.format()
        })

    '''
    @TODO-DONE:
    Create a POST endpoint to get questions based on a search term.
    It should return any questions for whom the search term
    is a substring of the question.

    TEST: Search by any phrase. The questions list will update to include
    only question that include that string within their question.
    Try using the word "title" to start.
    '''

    @app.route('/questions/search', methods=['POST'])
    def search_question():

        search_term = request.get_json()['searchTerm']
        # questions = Question.query.filter(Question.question.ilike(f'%{search_term}%')).all()
        questions = Question.query.filter(
            Question.question.ilike(
                '%{}%'.format(search_term))).all()
        result = [question.format() for question in questions]

        response = {
            "success": True,
            "total_questions": len(questions),
            "questions": result
        }

        print(response)

        return jsonify(response)

    '''
    @TODO-DONE:
    Create a GET endpoint to get questions based on category.

    TEST: In the "List" tab / main screen, clicking on one of the
    categories in the left column will cause only questions of that
    category to be shown.
    '''

    @app.route('/categories/<int:category_id>/questions')
    def get_question_by_category(category_id):
        selection = Question.query.filter(
            Question.category == category_id).order_by(
            Question.id).all()
        current_questions = paginate_questions(request, selection)
        current_category = Category.query.filter(Category.id == category_id)
        category_names = {}

        for category in current_category:
            category_names[str(category.id)] = category.type

        return jsonify({
            "success": True,
            "questions": current_questions,
            "total_questions": len(current_questions),
            "current_category": category_names
        })

    '''
    @TODO-DONE:
    Create a POST endpoint to get questions to play the quiz.
    This endpoint should take category and previous question parameters
    and return a random questions within the given category,
    if provided, and that is not one of the previous questions.

    TEST: In the "Play" tab, after a user selects "All" or a category,
    one question at a time is displayed, the user is allowed to answer
    and shown whether they were correct or not.
    '''

    @app.route('/quizzes', methods=['POST'])
    def play_trivia():
        body = request.get_json()
        previous_questions = body.get('previous_questions')
        quiz_category = body.get('quiz_category')
        category_id = quiz_category['id']
        # category_id = int(body["quiz_category"]["id"])

        try:
            if ((previous_questions is None) or (quiz_category is None)):
                abort(422)
                return jsonify({
                    'success': False
                })

            all_questions = Question.query.filter(
                Question.id.notin_(previous_questions)).all()
            category_questions = Question.query.filter(
                Question.category == category_id).filter(
                Question.id.notin_(previous_questions)).all()

            if (category_id == 0):
                questions = all_questions
            # elif len(category_questions) > 0:
            else:
                questions = category_questions

            if len(questions) > 0:
                next_question = questions[random.randint(
                    0, len(questions) - 1)].format()
            else:
                next_question = False

            return jsonify({
                'success': True,
                'question': next_question
            })

        except BaseException:
            abort(422)

    '''
    @TODO-DONE:
    Create error handlers for all expected errors
    including 404 and 422.
    '''

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "success": False,
            "error": 404,
            "message": "Page not found"
        }), 404

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            "success": False,
            "error": 400,
            "message": "Bad Request"
        }), 400

    @app.errorhandler(422)
    def unproccessable(error):
        return jsonify({
            "success": False,
            "error": 422,
            "message": "unproccessable"
        }), 422

    @app.errorhandler(405)
    def not_allowed(error):
        return jsonify({
            "success": False,
            "error": 405,
            "message": "method_not_allowed"
        }), 405

    @app.errorhandler(500)
    def internal_server(error):
        return jsonify({
            "success": False,
            "error": 500,
            "message": " Internal Server Error"
        }), 500

    return app

    # try:

    # except:
    #   db.session.rollback()
    #   abort(404)
    # finally:
    #   db.session.close()
