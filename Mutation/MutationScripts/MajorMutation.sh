#!/bin/bash

user_is_asking_for_help() {
    [[ "$1" == "-h" || "$1" == "--help" ]]
}

d4j_create_mml() {
  local USAGE='d4j_create_mml PROJECT BUG DEST'
  if user_is_asking_for_help "$@"; then
    echo "Usage: $USAGE"
    echo 'Prints the name of the newly created compiled MML file (e.g. 1.mml.bin).'
    return 0
  fi
  if [ "$#" != 3 ]; then
    echo "Usage: USAGE"
    return 1
  fi

  local PROJECT=$1
  local BUG=$2
  local DEST=$3

  local TEMPDIR
  TEMPDIR=$(mktemp -d "/tmp/mml-$PROJECT-XXXX") &&
  "$DEFECTS4J_HOME/framework/util/create_mml.pl" -p "$PROJECT" -b "$BUG" -o "$TEMPDIR" -c "$DEFECTS4J_HOME/framework/projects/$PROJECT/modified_classes/$BUG.src" &&
  mv "$TEMPDIR/$BUG.mml.bin" "$DEST" &&
  rm -rf "$TEMPDIR"
}

d4j_mutate() {
  local USAGE='d4j_mutate PROJECT BUG DIR'
  if user_is_asking_for_help "$@"; then
    echo "Usage: $USAGE"
    echo 'Compiles the Defects4J project in the current directory with mutants.'
    return 0
  fi
  if [ "$#" != 3 ]; then
    echo "Usage: $USAGE" >&2
    return 1
  fi

  local PROJECT=$1
  local BUG=$2
  local DIR=$(readlink --canonicalize "$3")

  local MML
  export MML=$(mktemp "$DIR/.mml.bin.XXXX") &&
  d4j_create_mml "$PROJECT" "$BUG" "$MML" &&
  (cd "$DIR" && 
   PATH="$PATH:$DEFECTS4J_HOME/major/bin" \
    ant -Dd4j.home="$DEFECTS4J_HOME" \
        -Dbasedir="$(pwd)" \
        -f "$DEFECTS4J_HOME/framework/projects/defects4j.build.xml" \
        mutate) &&
  rm -rf "$MML"
  unset MML
}

if user_is_asking_for_help "$1"; then
    echo "Usage: $0 [create|mutate] PROJECT BUG DIR"
    exit 0
fi

if [ "$#" -lt 3 ]; then
    echo "Error: Insufficient arguments provided."
    echo "Usage: $0 [create|mutate] PROJECT BUG DIR"
    exit 1
fi

PROJECT=$1
BUG=$2
DIR=$3

if [ ! -d "$DIR" ]; then
    echo "Error: Directory '$DIR' does not exist."
    exit 1
fi

d4j_mutate $PROJECT $BUG $DIR