#!/usr/bin/python3
# -*- coding: utf-8 -*-

# Par Charbel Kassis, p0976458,
#     Dorin Diaconu,  20017978.

## ch.py --- Un shell pour les hélvètes.

import os
import sys

def main ():
    
    # Demarrage shell pour les helvetes
    run_shell()


# Execute le shell pour les helvetes
def run_shell():

    sys.stdout.write("%% ")

    while True:

        pid = os.fork()
        
        # Cas du fork echouee
        if pid < 0:
            sys.stderr.write("Fork echouee \n")

        # Processus enfant. 
        # Lecture commande (avec arguments) au clavier et execution
        elif pid == 0:
            command = get_command()
            execute( command )

        # Processus parent. 
        # En attente jusqu'au fin execution processus enfant
        else:
            os.wait()


# Lecture commande au clavier et parsing
# Retourne: la commande (avec ces arguments) en forme d'une liste 1D ou 2D
def get_command():

    # Lecture commande
    cmd = input()

    # Parsing commande
    i = -1
    while True:

        i += 1
        if  i > len(cmd) - 1:
            break

        # Correction espaces autour arguments operateurs.
        if (i > 0 and cmd[i] == '>' and cmd[i-1] != ' ' 
            and cmd[i-1] != '>' and cmd[i-1] != '<'):
            cmd = cmd[:i] + ' >' + cmd[i+1:]
        if (i+1 < len(cmd) and cmd[i] == '>' and cmd[i+1] != ' ' 
            and cmd[i+1] != '>'):
            cmd = cmd[0:i] + '> ' + cmd[i+1:]
        if (i > 0 and cmd[i] == '<' and cmd[i-1] != ' ' and cmd[i-1] != '<'):
            cmd = cmd[:i] + ' <' + cmd[i+1:]
        if (i+1 < len(cmd) and cmd[i] == '<' and cmd[i+1] != ' ' 
            and cmd[i+1] != '<' and cmd[i+1] != '>'):
            cmd = cmd[0:i] + '< ' + cmd[i+1:]
        
        # Correction argument '*'. Change 'ls **' en 'ls * *'
        if (i+1 < len(cmd) and  cmd[i] == '*' and cmd[i + 1] == '*'):
            cmd = cmd[:i] + cmd[i+1:]
            i -= 1

        # Correction espaces autour argument '|'
        if (i > 0 and cmd[i] == '|' and cmd[i-1] != ' ' and cmd[i-1] != '|'):
            cmd = cmd[:i] + ' |' + cmd[i+1:]
        if (i+1<len(cmd) and cmd[i]=='|' and cmd[i+1]!=' ' and cmd[i+1]!='|'):
            cmd = cmd[0:i] + '| ' + cmd[i+1:]

    return cmd.split()


# Execute une commande
# Entree: cmd, une commande a executer
def execute( cmd ):

    # Terminer processus s'il n'y a aucune instruction
    if len( cmd ) == 0:
        os.abort()

    # Convertion operateurs * , > , < , |
    cmd = modify_args( cmd )

    # Verifie si la commande est correcte et execution
    path     = findPath( cmd[0] )
    if path != False:
        os.execvp(cmd[0], cmd)

    # Terminer le processus-enfant en cas d'une commande inconnue
    else:
        sys.stdout.write ("Commande inconnue\n")
        os.abort()


# Modifie la liste des arguments pour tenir comptes des operateurs *,>,<,|
# Effectue l'expansion d'arguments, la pipeline et la redirection.
# Entree:   cmd, une commande a executer.
# Retourne: la commande (avec arguments) en forme de liste a executer
def modify_args( cmd ):

    for i, item in enumerate(cmd):
        
        # Expansion arguments 
        if item == '*':
            cmd = expansion(cmd, i)

        # Effectue la pipeline
        if item == '|':
            pipeline(cmd, i)
        
        # Redirection
        if (item == '<' or item == '>') and i + 1 < len(cmd):
            redirect( cmd[i+1], item )
            cmd[i]   = ' '
            cmd[i+1] = ' '

    return normalize( cmd )


# Cherche le chemin d'une commande.
# Entree:   cmd, le nom de commande (sans arguments)
# Retourne: nom chemin ou False.
def findPath( cmd ):
    
    allPath = os.get_exec_path( env = None )

    for i in range( len(allPath) ):
        file       = os.path.join(allPath[i], cmd)
        fileExists = os.path.isfile(file) 
        
        if(fileExists):
            return file

    return False


# Expansion arguments. Remplace * par les documents du repertoire courant.
# Entrees: cmd, la commande (avec arguments); i, l'indexe de l'operateur *.
# Retourne: la commande et les arguments en forme d'une liste.
def expansion( cmd, i ):
    
    current_folder = os.getcwd()
    folder         = os.listdir( current_folder )
    cmd[i]         = folder

    return cmd


# Convertion commande d'une liste 2D en liste 1D.
# Entree: cmd, la commande a convertir
# Retourne: une liste unidimensionnelle d'arguments sans arguments vides.
def normalize( cmd ):

    flattened_args = []
    for i in cmd:
        if isinstance(i, list):
            for item in i:
                flattened_args.append(item)
        else:
            flattened_args.append(i)

    # Enleve les arguments vides comme ' '
    flattened_args[:] = [x for x in flattened_args if x != ' '] 

    return flattened_args


# Traite les <, >. Modifie l'i/o qui est le shell par defaut.
# Entree: fileName, le nom fichier; direction, la direction de la redirection
def redirect( fileName, direction ):

    try:
        if  direction == '<':
            newInput = os.open(fileName, os.O_RDONLY)
            os.dup2(newInput, sys.stdin.fileno())
            os.close(newInput)

        elif direction == '>':
            newOutput = os.open(fileName, os.O_WRONLY|os.O_CREAT|os.O_TRUNC)
            os.dup2(newOutput, sys.stdout.fileno())
            os.close(newOutput)

    except IOError:
        print ('Impossible de traiter le fichier')
        os.abort()


# Effectue la pipeline entre 2 instructions.
# Entrees: cmd, les commandes divisees par |; i, l'indexe de l'operateur |.
def pipeline( cmd, i ):

    r, w = os.pipe()
    pid  = os.fork()
    
    # Cas du fork echouee
    if pid < 0:
        sys.stderr.write("Fork echouee \n")

    # Processus-enfant.
    # Execution de la premiere instruction. Ecriture output dans la pipe.
    elif pid == 0 :
        
        os.close(r)
        
        # L'instruction avant operateur "|"
        child_cmd = cmd[:i]

        # l'input va etre passe au pipe au lieu du shell
        os.dup2(w, sys.stdout.fileno())
        os.close(w)
        
        execute(child_cmd)
    
    # Processus-parent.
    # Execution de la deuxiemme instruction. Lecture input dans la pipe.    
    else:
        os.wait()
        os.close(w)
        
        # L'input va etre lu dans la pipe au lieu du shell
        os.dup2(r, sys.stdin.fileno())
        os.close(r)
            
        # L'instruction apres operateur "|"
        parent_cmd = cmd[i+1:]

        execute(parent_cmd)
        

# Demarrage programme et l'interruption du clavier (Ctrl+C) 
try:
    main ()

except KeyboardInterrupt:
    sys.exit(0)