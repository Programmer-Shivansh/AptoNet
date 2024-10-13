CC = gcc
CFLAGS = -Wall -O2
TARGET = vport

all: $(TARGET)

$(TARGET): src/vport.c
	$(CC) $(CFLAGS) -o $(TARGET) src/vport.c

clean:
	rm -f $(TARGET)
