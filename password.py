import secrets
import string
import re

from nltk.corpus import wordnet
from pyhibp import pwnedpasswords as pw
from pyhibp import set_user_agent

from settings import EXCLUDED_WORDS, USABLE_CHARS, EXCLUDED_CHARS, MAX_PASS_LEN, MIN_PASS_LEN, FIXED_LEN, PSWRD_NO
from language import Language

class PyPass:
	"""
	Class used for storing and generating passwords.

	One or more passwords are generated with self.generate_password() [stored in the self.passwords] 
	or self.generate_human_password() [stored in the self.human_passwords].
	"""

	def __init__(self, usable_chars=USABLE_CHARS, excluded_chars=EXCLUDED_CHARS, min_pass_len=MIN_PASS_LEN,
				 max_pass_len=MAX_PASS_LEN, excluded_words=EXCLUDED_WORDS, remove_repeating=False,
				 remove_english=False, ensure_proportions=False, language_lib=None, include_whitespace=True):
		"""
		Args: 
			usable_chars (list): list of lists containing arrays of characters to be used in password generation. 
								 Is not relevant in generating passwords from language model.
			excuded_chars (list): list of characters which will not be used in password generation. 
								  Is not relevant in generating passwords from language model.
			min_pass_len (int): Minimum length of any password generated by this class.
			max_pass_len (int): Maximum length of any password generated by this class.
			excluded_words (list): List of words(str) which will not be used in password generation. 
								   Is not relevant in generating passwords from language model.
			remove_repeating (bool): Determines if repeating characters will be removed from password.
								 	 Is not relevant in generating passwords from language model.
			remove_english (bool): Determines if English language words, with len more than 3 will be removed from password.
								   Is not relevant in generating passwords from language model.
			ensure_proportions (bool): Determines if the rule that the password must have at least one of each group from
									   usable_chars list will be enforced. Is not relevant in generating passwords from language model.
			language_lib (str): Name of the language model to be used in generating language model passwords.
			include_whitespace (bool): Determines if the whitespaces will be included in the passwords generated by the
									   language model.
		"""

		self.excluded_chars = excluded_chars

		"""
		Usable chars are checked against the excluded characters, and any matching chars are removed before
		initializing usable_chars property.
		"""
		for excl_char in excluded_chars:
			for usable_char_list in usable_chars:
				if excl_char in usable_char_list:
					usable_char_list.remove(excl_char)

		self.usable_chars = usable_chars
		self.excluded_words = excluded_words

		# Setting the minimum and maximum length of the generated passwords.
		self.min_pass_len = min_pass_len
		self.max_pass_len = max_pass_len

		# Passwords generated with self.generate_human_password will be stored here
		self.human_passwords = []
		# Passwords generated with self.generate_password will be stored here
		self.passwords = []

		self.language_manager = Language(library=language_lib, min_sentence_length=min_pass_len, max_sentence_length=max_pass_len, include_whitespace=include_whitespace) if language_lib is not None else None

		set_user_agent(ua="PyPass Python password generator. Demo version.")


	def __str__(self):
		return ' '.join(self.all_passwords)

	@property
	def all_passwords(self):
		# Returns combined "human" and "random" passwords.
		return self.passwords + self.human_passwords

	def generate_random(self, pass_length):
		"""
		Generates a random list of chars from types available in usable_chars.
		
		Args:
			pass_length (int): length of random passwords string to be generated.
		"""
		
		return [secrets.choice(self.usable_chars[self.usable_chars.index(secrets.choice(self.usable_chars))]) for e in range(pass_length)]

	def remove_touching_duplicates(self, my_string_list):
		"""
		This function removes two same characters which are placed one after the other,
		replacing them with random char from a randomly chosen usable_char list.
		
		Args:
			my_string_list (list): list of characters.
		"""
		new_string_list = []
		
		# The -1 range was chosen to avoid index out of range error.
		for char in range(len(my_string_list[:-1])):
			if my_string_list[char] == my_string_list[char+1]:
				new_string_list.append(secrets.choice(self.usable_chars[self.usable_chars.index(secrets.choice(self.usable_chars))]))
			else:
				new_string_list.append(my_string_list[char])

		new_string_list.append(my_string_list[-1])

		return(new_string_list)



	def contains_excluded(self, my_string):
		"""
		Checks if a string contains any of the words or other char sequences stored in self.excluded_words.
		"""
		
		return any(word in my_string for word in self.excluded_words)


	def find_letter_sequences(self, my_list):
		"""
		Used in generate_human_password(). Finds sequences of letters in the password string. Once found, 
		it checks if the letter sequence corresponds to an English word, or is an excluded word. If such 
		sequences are found, they are replaced with a random set of characters.

		Args:
			my_list (list): list representation of the password.
		"""

		pass_string = ''.join(my_list)
		pattern = re.compile('[a-zA-Z]{2,}')

		"""
		Replaces English words with new random strings.
		The process is repeated if the newly generated random string, is also an English word.
		"""

		finds = 1

		while finds == 1:
			matches = pattern.findall(pass_string)
			if len(matches) > 0:
				for m in matches:
					if (wordnet.synsets(m.lower()) or self.contains_excluded(m)) and len(m) > 3:
						pass_string = pass_string.replace(m, self.remove_touching_duplicates(self.generate_random(len(m))))
						finds = 1

					else:
						finds = 0
			else:
				finds = 0

		return list(pass_string)


	def remove_english(self, my_string_list, remove_touching):
		"""
		Used in generate_password(). Finds sequences of letters in the password string. Once found,
		it checks if the letter sequence corresponds to an English word. If such sequences are found, 
		they are replaced with a random set of characters.

		Args:
			my_string_list (list): list representation of the password.
			remove_touching (bool): Determines if touching duplicate characters will be removed.
		"""
		pass_string = ''.join(my_string_list)
		pattern = re.compile('[a-zA-Z]+')

		"""
		Replaces English words with new random strings.
		The process is repeated if the newly generated random string, is also an English word.
		"""

		finds = 1

		while finds == 1:
			matches = pattern.findall(pass_string)
			if len(matches) > 0:
				for m in matches:
					if wordnet.synsets(m.lower()) and len(m) > 3:
						if remove_touching:
							pass_string = pass_string.replace(m,
															  self.remove_touching_duplicates(self.generate_random(len(m))))
						else:
							pass_string = pass_string.replace(m, self.generate_random(len(m)))
						finds = 1

					else:
						finds = 0
			else:
				finds = 0

		return list(pass_string)


	def remove_excluded(self, my_string_list, remove_touching):
		"""
		Used in generate_password(). Finds sequences of letters in the password string.	Once found, 
		it checks if the letter sequence corresponds to an item from the excluded words list (self.excluded_words).
		If such sequences are found, they are replaced with a random set of characters.
		Args:
			my_string_list (list): list representation of the password.
			remove_touching (bool): Determines if touching duplicate characters will be removed.
		"""

		pass_string = ''.join(my_string_list)
		pattern = re.compile('[a-zA-Z]+')

		"""
		Replaces English words with new random strings.
		The process is repeated if the newly generated random string, is also an English word.
		"""

		finds = 1

		while finds == 1:
			matches = pattern.findall(pass_string)
			if len(matches) > 0:
				for m in matches:
					if self.contains_excluded(pass_string) and len(m) > 3:
						if remove_touching:
							pass_string = pass_string.replace(m,
															  self.remove_touching_duplicates(
																  self.generate_random(len(m))))
						else:
							pass_string = pass_string.replace(m, self.generate_random(len(m)))
						finds = 1

					else:
						finds = 0
			else:
				finds = 0

		return list(pass_string)

	@staticmethod
	def confirm_proportions(list_dict):
		"""
		Examines if there is at least one character from each usable_chars list. 
		Returns True if the proportion is fulfilled, and False if not.

		Args:
			list_dict (list): List of dictionaries generated by the generate_new_dict method.
		"""
		return all(type_freq >= 1 for type_freq in list_dict.values())

	def generate_new_dict(self, string_members):
		"""
		Generates a new dictionary reflecting the number of each char type from usable_chars in the password.

		Args:
			string_members (list): list of characthers representing the password.
		"""
		return {str(self.usable_chars.index(v)): sum(ch in v for ch in string_members) for v in self.usable_chars}

	def ensure_proportions(self, string_members):
		"""
		Checks if there is at least one of each types of usable_chars in the password string using the confirm_proportions().
		If the proportion is not fulfilled, it replaces a random character in the password string, with a randomly chosen
		char from the missing usable_chars type. It continues this check until the confirm_proportions() returns True.
		Does not check for enforcing exclusion of English words or consecutive chars, because this function will insert only
		a single character from a list, from which not a single member is contained in the generated password. It will check
		for excluded words, since these might be a sequence of different types of chars.

		Args:
			string_members (list): list of characthers representing the password.
		"""
		string_proportions = self.generate_new_dict(string_members)

		while not self.confirm_proportions(string_proportions):
			for item in string_proportions.keys():

				if string_proportions[item] < 1:
					index = secrets.choice(list(range(len(string_members))))
					string_members[index] = secrets.choice(self.usable_chars[int(item)])

					# If excluded words are defined, the function will remove any contained in the new password.
					if len(self.excluded_words) > 0:
						string_members = self.remove_excluded(string_members, remove_touching=False)

				string_proportions = self.generate_new_dict(string_members)

		return string_members

	def generate_human_password(self, pass_number=PSWRD_NO, fixed_len=FIXED_LEN):
		"""
		The function will generate a password conforming to most common rules recommended for passwords generation. 
		The idea is to generate passwords which are resistant to breaking attempts where the malicious actor presumes 
		that the password wa generated by a person and not a randomizing program.
		
		Therefore, it should be noted that, because the function implements the rules listed below, the number of possible
		combinations this function generates is lower that a more pure randomization function (see generate_password()). 
		So, once again, using this function is recommended only if the user wishes to protect themselves particularly from 
		cracking attempts modified to presume a person generated a password.
			
		Implements other functions in order to generate a random string containing:
			1) characters are only lower and upper case ascii letters, numbers or punctuation signs;
			2) at least one of each char type from item 1) is contained withing the password string;
			3) there are no sequences of same chars in the password string;
			4) no char sequence is either an English word, nor does it belong to the list of sensitive words defined by user;
			5) after implementing rules 1)-4), the password is checked against database from 
				'https://haveibeenpwned.com/Passwords', to ensure its not contained in the database of passwords previously 
				exposed in data breaches.
		
		Generated passwords are appended to self.human_passwords
		
		Args:

			pass_number (int): Designates how many passwords are to be created. If left blank, will generate one password.
			fixed_len (int): Determines if password needs to be of a designated fixed length.
		"""

		# Prevents setting password number below 1.
		if pass_number < 1:
			pass_number = 1

		for number in range(pass_number):

			if fixed_len:
				pass_string_list = self.generate_random(fixed_len)

			else:
				pass_len_range = list(range(self.min_pass_len,self.max_pass_len+1))
				pass_string_list = self.generate_random(secrets.choice(pass_len_range))


			# Removing touching duplicate chars.
			my_pass = self.find_letter_sequences(self.remove_touching_duplicates(pass_string_list))

			# Ensuring at least one member of each type from usable_chars is contained in the password string.
			my_pass = self.ensure_proportions(my_pass)

			my_pass = ''.join(my_pass)

			# Checking if the generated password was exposed in data breaches. If so, the process is repeated.
			if pw.is_password_breached(password=my_pass) != 0:
				self.generate_password()
			else:
				self.human_passwords.append(my_pass)


	def generate_password(self, pass_number=PSWRD_NO, remove_repeating=False, remove_english=False, check_proportions=False,
					  fixed_len=FIXED_LEN):

		"""
		The function will generate a password string from the set of usable characters described by the user in settings.py.
		Generated passwords are appended to self.passwords.        

        Args:
			pass_number (int): Designates how many passwords are to be created. If left blank, will generate one password.
			remove_repeating (bool): Determines if consecutive duplicate chars will be removed from the password. 
									 If left blank, duplicates will not be removed.
			remove_english (bool): Designates if English words will be removed from the password. If left blank, 
								   English words will not be removed.	
			ensure_proportions (bool): Designates if the password will contain at least one char form each list 
									   in usable_chars. If left blank, these proportions will not be enforced.
			fixed_len (int): Will determine a fixed length of the generated password.
		"""

		# Prevents setting password number below 1.
		if pass_number<1:
			pass_number = 1

		for number in range(pass_number):
			if fixed_len:
				pass_string_list = self.generate_random(fixed_len)

			else:
				pass_len_range = list(range(self.min_pass_len,self.max_pass_len+1))
				pass_string_list = self.generate_random(secrets.choice(pass_len_range))

			# Removing touching duplicate chars, in case the user chose so.
			if remove_repeating:
				pass_string_list = self.remove_touching_duplicates(pass_string_list)

			# Removing English words and excluded words, if the user chose so.
			if remove_english:
				pass_string_list = self.remove_english(pass_string_list,remove_repeating)

			# Removing excluded words, if they are designated by the user.
			if len(self.excluded_words) > 0:
				pass_string_list = self.remove_excluded(pass_string_list, remove_repeating)

			# If the user chose so, ensuring at least one member of each group of characters
			# from the usable characters lists has been included.
			if check_proportions:
				pass_string_list = self.ensure_proportions(pass_string_list)

			my_pass = ''.join(pass_string_list)

			if pw.is_password_breached(password=my_pass) != 0:
				self.generate_password(pass_number=pass_number, remove_repeating=remove_repeating,
									   remove_english=remove_english, ensure_proportions=check_proportions)
			else:
				self.passwords.append(my_pass)

	def generate_sentence_pass(self, pass_number=PSWRD_NO):
		"""
		Function will generate passwords in form of random sentences, generated using one of the custom stored or nltk trigram models
		Generated passwords are appended to self.passwords.

        Args:
			pass_number (int): Designates how many passwords are to be created. If left blank, will generate one password.		
		"""
		for number in range(pass_number):
			my_pass = self.language_manager.form_sentece()
			if pw.is_password_breached(password=my_pass) != 0:
				self.generate_sentence_pass(pass_number=pass_number)
			else:
				self.passwords.append(my_pass)
