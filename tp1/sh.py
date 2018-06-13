#!/usr/bin/python3
# -*- coding: utf-8 -*-

# Par Charbel Kassis p0976458
# Par Dorin Diaconu

## ch.py --- Un shell pour les hélvètes.

import os
import sys

def main ():
	sys.stdout.write("%% ") 
	run_shell()       # demarrage shell pour les helvetes


# Demarre le shell pour les helvetes
def run_shell():
	while True:
		new_process() # execution commande
		

# Lecture commande dans la ligne de commande
def read_command():
	
	command = input().split()
	return command


# Cree un nouveau process (execution commande)
def new_process():
	pid = os.fork()                       # cree un nouveau processus-enfant
	
	if pid == 0 :
		user_input = read_command() # lit une commande
		process_user_input(user_input) # traite le resultat user_input
	else :
		os.waitpid(pid, 0) 				  # le processus parent est mit en attente

# Lis une instruction separee mot par mot dans un tableau et effectue les taches necessaires
def process_user_input(user_input):

	if( len(user_input) == 0): # S'il n'y a aucune instruction, alors terminer.
		os.abort()

	command          = user_input[0] # le programme a execute doit etre le premier argument
	args             = user_input

	path = findPath(command)          # le chemin de la commande
		
	if path != False :                # verifie si la commande est valide
		execute_command( path, command, args )
	else :
		messageErreur = "Commande "+ command + " inconnue\n"
		sys.stdout.write (messageErreur)
		os.abort()                    # force de terminer le processus-enfant


# Execute une commande
def execute_command( path, command, args ):
	
	# Modifie les arguments passe par l'utilisateur pour tenir compte des * , > , < , |
	args = modify_args( args )

	# Execution commande incluant les arguments
	os.execvp(command, args)

# Modifie le tableau des arguments pour tenir comptes des caracteres speciaux * , > , < , |
def modify_args( args ):

	for i, item in enumerate(args):
		
		if item == '*':
			
			expansion(args,i)

		if item == '|':

			pipeline(args,i)
				
		if item[0] == '>':
				
			redirectOutput(item,args,i)
		
		elif item[0] == '<':

			args[i] = item[1:]

	return args


# Cherche le chemin d'une commande
# Retourne: nom chemin ou False
def findPath(fileName):
	
	allPath = os.get_exec_path( env = None )

	for i in range( len(allPath) ):

            file       = os.path.join(allPath[i], fileName)
            fileExists = os.path.isfile(file) 
		
            if(fileExists):

                return file

	return False


# Traite les * dans les arguments. * sera remplacer par tous les documents dans le repertoire courant.
def expansion(args,i):
	
	current_folder = os.getcwd()
	folder         = os.listdir( current_folder )
	folder.sort()  # trie les elements en ordre ascendent
	args[i]        = folder

	
	# Conversion liste 2D en liste 1D
	flattened_args = []
	for i in args:
		if isinstance(i, list):
			for item in i:
				flattened_args.append(item)
		else:
			flattened_args.append(i)
	args = flattened_args

# Traite les > dans les arguments. Modifie l'output qui est le shell par defaut.
def redirectOutput(item,args,i):

	fileName = item[1:]
	newOutput = os.open(fileName, os.O_WRONLY|os.O_CREAT|os.O_TRUNC)
	os.dup2(newOutput, sys.stdout.fileno())
	args.pop(i)

# Traite les | dans les arguments. Pipeline: connecte la sortie de la premiere 
#instruction avec l'entree de la deuxieme instruction
def pipeline(args,i):

	r, w = os.pipe()
	pid = os.fork()
	
	# l'enfant s'occupe d'execute la premiere instruction, il doit d'abord fermer la lecture dans le pipe
	#puis redigire la sortie de l'execution vers "w" au lieu du shell.
	if pid == 0 :
		
		os.close(r)
		w = os.fdopen(w, 'w')
		
		# l'instruction de l'enfant est la premiere partie du tableau "args" , c'est-a-dire tout
		#ce qui se trouve avant le premier "|"
		child_args = args[:i]

		# l'input va etre passe au "w" au lieu du shell
		os.dup2(w.fileno(), sys.stdout.fileno())
		process_user_input(child_args)
		
	# le parent s'occupe de lire le resultat, il ferme l'ecriture puis lis le resultat obtenu par l'enfant.
	#le resultat est ensuite "split" dans un tableau puis ajouter aux arguments.
	else:
		os.waitpid(pid,0)
		os.close(w)
		r = os.fdopen(r)
		
		# L'input va etre lu dans "r" au lieu du shell
		os.dup2(r.fileno(), sys.stdin.fileno())
			
		# l'instruction du parent est la deuxieme partie du tableau "args"
		parent_args = args[i+1:]

		process_user_input(parent_args)
		
		
try:
	main ()
except KeyboardInterrupt:
	sys.exit(0)
