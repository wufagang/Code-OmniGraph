# 示例Python文件
class UserService:
    def __init__(self, db_connection):
        self.db = db_connection
    
    def get_user(self, user_id):
        """根据用户ID获取用户信息"""
        query = f"SELECT * FROM users WHERE id = {user_id}"
        return self.db.execute(query)
    
    def create_user(self, name, email):
        """创建新用户"""
        if not self.validate_email(email):
            raise ValueError("Invalid email")
        
        query = f"INSERT INTO users (name, email) VALUES ('{name}', '{email}')"
        return self.db.execute(query)
    
    def validate_email(self, email):
        """验证邮箱格式"""
        return "@" in email

# 主函数
def main():
    service = UserService(None)
    user_input = input("Enter user ID: ")
    user = service.get_user(user_input)
    print(f"User: {user}")

if __name__ == "__main__":
    main()
