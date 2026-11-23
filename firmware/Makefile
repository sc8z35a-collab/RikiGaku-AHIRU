CC = gcc
CFLAGS = -std=c11 -O2 -Wall -Wextra -Werror -pedantic -fsanitize=address,undefined

all: test_sil_rev3

test_sil_rev3: fadec_rev3.c test_sil_rev3.c fadec_rev3.h
	$(CC) $(CFLAGS) fadec_rev3.c test_sil_rev3.c -lm -o test_sil_rev3

check: test_sil_rev3
	cppcheck --enable=warning,performance,portability --error-exitcode=1 fadec_rev3.c
	clang --analyze fadec_rev3.c
	./test_sil_rev3

clean:
	rm -f test_sil_rev3 *.plist
