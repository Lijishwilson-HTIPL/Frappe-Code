# Copyright (c) 2026, Quality Team and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

from quality_dms.dms.doctype.training_settings.training_settings import get_pass_percentage


class DMSQuiz(Document):

	def validate(self):
		if not self.pass_percentage:
			self.pass_percentage = get_pass_percentage()

	def get_effective_pass_percentage(self):
		return self.pass_percentage or get_pass_percentage()

	def get_questions_for_display(self):
		"""Return the quiz questions for an employee to answer, WITHOUT the
		correct answers (never send the answer key to the client)."""
		questions = []
		for q in self.questions:
			options = [q.option_1, q.option_2, q.option_3, q.option_4]
			questions.append({
				"question_text": q.question_text,
				# only include options that are actually filled in
				"options": [o for o in options if o not in (None, "")],
			})
		return questions

	def grade(self, answers):
		"""Grade submitted answers and return the score as a percentage.

		`answers` maps the question's zero-based index (as a string or int) to
		the selected option number ("1".."4"). Score is marks-weighted:
		earned marks / total marks * 100. A question with no `marks` set counts
		as 1 mark so every quiz can be graded even if marks were left blank."""
		total_marks = 0.0
		earned_marks = 0.0
		for idx, q in enumerate(self.questions):
			marks = q.marks or 1
			total_marks += marks
			selected = answers.get(str(idx))
			if selected is None:
				selected = answers.get(idx)
			if selected is not None and str(selected) == str(q.correct_option):
				earned_marks += marks
		if total_marks == 0:
			return 0.0
		return round(earned_marks / total_marks * 100, 2)
