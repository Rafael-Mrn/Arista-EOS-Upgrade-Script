netmiko.exceptions.ReadTimeout

when output is not the expected output.

Yes, Netmiko itself is synchronous and connects to one device per thread, but you can achieve concurrent connections to multiple devices simultaneously by pairing it with Python's standard `concurrent.futures` module (multithreading).

Here is how you can run Netmiko commands across multiple devices in parallel:

```python
from concurrent.futures import ThreadPoolExecutor, as_completed
from netmiko import ConnectHandler
from netmiko.ssh_exception import NetmikoAuthenticationException, NetmikoTimeoutException

# Define your device list
devices = [
    {
        "device_type": "cisco_ios",
        "host": "172.16.10.11",
        "username": "admin",
        "password": "cisco123",
    },
    {
        "device_type": "cisco_ios",
        "host": "172.16.10.12",
        "username": "admin",
        "password": "cisco123",
    },
]

def execute_command(device):
    """Worker function to connect to a single device and send commands."""
    host = device["host"]
    try:
        with ConnectHandler(**device) as connection:
            connection.enable()
            output = connection.send_command("show ip int brief")
            return f"=== Output from {host} ===\n{output}"
    except (NetmikoTimeoutException, NetmikoAuthenticationException) as error:
        return f"[Error] Failed to connect to {host}: {error}"

# Run connections concurrently
max_threads = 5  # Adjust based on the number of target devices

with ThreadPoolExecutor(max_workers=max_threads) as executor:
    # Submit all connection tasks to the thread pool
    futures = [executor.submit(execute_command, dev) for dev in devices]
    
    # Process results as each device finishes
    for future in as_completed(futures):
        print(future.result())

```

**Key Advantages:**

* **`ThreadPoolExecutor`**: Spawns independent threads for each device connection so network latency or slow responses from one switch won't block the others.
* **Context Manager (`with ConnectHandler`)**: Automatically closes the SSH connection even if errors occur during command execution.
* **`as_completed()`**: Yields results immediately as soon as any device completes its task, rather than waiting for the entire queue in order.

Explanation of ThreadPoolExecutor in the context of this program:

In this program, lines 42–46 are:
```python
42  with ThreadPoolExecutor(max_workers=max_threads) as executor:
43      # Submit all connection tasks to the thread pool
44      futures = [executor.submit(execute_command, dev) for dev in devices]
45
46      # Process results as each device finishes
```

### Line 42

```python
with ThreadPoolExecutor(max_workers=max_threads) as executor:
```

This creates a thread pool that can run up to `max_threads` tasks at the same time.

Earlier, the program sets:

```python
max_threads = 5
```

Therefore, the executor can use up to five worker threads. Since `devices` contains two devices, only two threads are needed for this run.

The `with` statement ensures that the executor is properly shut down when the indented block finishes. It waits for submitted work to complete and cleans up the worker threads.

The executor is assigned to the variable `executor`, which is used on line 44 to submit work.

### Line 43

```python
# Submit all connection tasks to the thread pool
```

This comment describes the next line. A task consists of:

- Calling `execute_command`
- Passing one device dictionary to it
- Running that function in a worker thread

### Line 44

```python
futures = [executor.submit(execute_command, dev) for dev in devices]
```

This loops through every device in the `devices` list.

For each device, this part runs:

```python
executor.submit(execute_command, dev)
```

`submit()` schedules `execute_command(dev)` to run in one of the executor’s worker threads. It returns a `Future` object immediately.

A `Future` is a placeholder representing work that has been submitted but may still be running. It can later provide:

- The function’s return value
- An exception raised by the function
- The completion status of the task

The list comprehension creates one `Future` for each device and stores them in `futures`.

Conceptually, this:

```python
futures = [executor.submit(execute_command, dev) for dev in devices]
```

is similar to:

```python
futures = []

for dev in devices:
    future = executor.submit(execute_command, dev)
    futures.append(future)
```

The important point is that `submit()` does not wait for the device connection to finish. Both device tasks are scheduled, allowing their connections and commands to run concurrently.

### Line 45

This is a blank line used for readability. It has no effect on execution.

### Line 46

```python
# Process results as each device finishes
```

This comment describes the loop beginning on line 47:

```python
for future in as_completed(futures):
```

`as_completed(futures)` yields each `Future` as soon as its associated device task finishes.

The results are therefore handled in completion order, not necessarily in the same order as the devices list. For example, if the second device responds first, its output is printed first.

On line 48:

```python
print(future.result())
```

`future.result()` retrieves the value returned by `execute_command()`. In this program, that value is either the command output or a connection-error message.

Overall, the flow is:

1. Submit one task per device.
2. Let the worker threads run those tasks concurrently.
3. Wait for each task to finish.
4. Print each result as soon as it becomes available.

## Helpful Definitions for this project

**Function**  
A reusable block of code.

```python
def greet():
    print("Hello")
```

**Function call**  
Running a function. Parentheses mean “run it now.”

```python
greet()
```

**Function object**  
The function itself, without running it. Useful when passing a function to another function.

```python
executor.submit(greet)
```

**Parameter**  
A variable listed in a function definition.

```python
def greet(name):
    # name is a parameter
    print(name)
```

**Argument**  
The actual value provided when calling a function.

```python
greet("Rafael")
```

`"Rafael"` is an argument.

**Positional argument**  
An argument matched by its position.

```python
copyEOStoFlash("EOS-4.34.4M", "192.168.0.6", device)
```

The first value goes to the first parameter, the second to the second parameter, and so on.

**Keyword argument**  
An argument matched by parameter name.

```python
copyEOStoFlash(
    EOS_VERSION="EOS-4.34.4M",
    httpServerIP="192.168.0.6",
    device=device,
)
```

**`parameter=value`**  
The syntax for providing a keyword argument.

```python
name="Rafael"
```

It means: put `"Rafael"` into the parameter named `name`.

**`*args`**  
Collects extra positional arguments into a tuple.

```python
def example(*args):
    print(args)
```

**`**kwargs`**  
Collects extra keyword arguments into a dictionary.

```python
def example(**kwargs):
    print(kwargs)
```

**Unpacking with `*`**  
Turns a tuple or list into separate positional arguments.

```python
values = ("one", "two")
example(*values)
```

This behaves like:

```python
example("one", "two")
```

**Unpacking with `**`**  
Turns a dictionary into separate keyword arguments.

```python
options = {"name": "Rafael", "age": 30}
example(**options)
```

This behaves like:

```python
example(name="Rafael", age=30)
```

**`device=dev`**  
Assigns the current device stored in `dev` to the worker’s `device` parameter.

```python
executor.submit(copyEOStoFlash, device=dev)
```

**`executor.submit()`**  
Schedules a function to run, possibly on another thread.

```python
executor.submit(copyEOStoFlash, device=dev)
```

It does not immediately return the function’s result.

**`ThreadPoolExecutor`**  
A tool that runs multiple functions concurrently using worker threads.

```python
with ThreadPoolExecutor(max_workers=3) as executor:
    ...
```

**Worker function**  
The function performed by each thread. In your project:

```python
copyEOStoFlash
```

**`Future`**  
An object representing work that has been scheduled or is still running.

```python
future = executor.submit(...)
```

**`future.result()`**  
Gets the worker function’s returned result after it finishes.

**`as_completed()`**  
Loops through futures in the order they finish, not necessarily the order they were submitted.

```python
for future in as_completed(futures):
    print(future.result())
```

**`len(devices)`**  
Returns the number of items in `devices`.

```python
max_threads = len(devices)
```

**Empty list**  
A list containing no items.

```python
devices = []
```

The executor checks this so it does not try to create a thread pool with zero workers.