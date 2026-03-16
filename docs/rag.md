@../../core/cagr_processor/embedding_worker/ 这个模块现在直接写的qdrant_client 类进行向量数据库操作，这种写法太简单了， 我现在需要按照一下要求完成，
    1. 这个模块能扩展不同的向量数据库
        定义这么一个接口 VectorDatabase，其中包括一下功能(方法)
        createCollection
        createHybridCollection
        dropCollection
        hasCollection
        listCollections 
        insert
        insertHybrid
        search
        hybridSearch
        delete
        query
        checkCollectionLimit
    2. 你可以自己定义这些方法需要的参数和返回值的model
    3. 这个模块你要实现两个向量数据库的支持， qdrant和milvus， 实现中一定不允许存在固定的字符串，比如需要一下链接url，username， password 使用config类进行传递
    4. 写实现的时候注意性能和一些异常情况的考虑
这次的代码都要在这个模块内完成