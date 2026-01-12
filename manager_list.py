import multiprocessing

def worker(shared_list, value):
    shared_list.append(value)

if __name__ == '__main__':
    with multiprocessing.Manager() as manager:
        shared_list = manager.list()  # Create a shared list

        processes = []
        for i in range(5):
            p = multiprocessing.Process(target=worker, args=(shared_list, i))
            processes.append(p)
            p.start()

        for p in processes:
            p.join()

        print(f"Final shared list: {list(shared_list)}")