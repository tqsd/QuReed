import simpy


def consumer(env, storeA, storeB):
    while True:
        print("Waiting...")
        e = yield simpy.events.AnyOf(env, [storeA.get(), storeB.get()])
        print("Got:", e)


env = simpy.Environment()
storeA = simpy.Store(env)
storeB = simpy.Store(env)
env.process(consumer(env, storeA, storeB))


def send(env):
    yield env.timeout(1)
    print("Putting in B")
    storeB.put("sigB")
    yield env.timeout(1)
    print("Putting in A")
    storeA.put("sigA")


env.process(send(env))
env.run(until=5)
