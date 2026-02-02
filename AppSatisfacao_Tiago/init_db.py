import sqlite3
import os

DATABASE = "database.db"

def init_database():
    """Inicializar base de dados com tabela de satisfação"""
    
    # Remover base de dados antiga se existir
    if os.path.exists(DATABASE):
        os.remove(DATABASE)
        print(f"Base de dados antiga removida.")
    
    # Conectar e criar tabela
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Criar tabela com constraints apropriadas
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS satisfacao (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            grau TEXT NOT NULL CHECK(grau IN ('Muito satisfeito', 'Satisfeito', 'Insatisfeito')),
            data DATE NOT NULL DEFAULT CURRENT_DATE,
            dia_semana TEXT NOT NULL,
            hora TIME NOT NULL DEFAULT CURRENT_TIME,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Criar índices para melhor performance
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_data ON satisfacao(data)
        """)
        
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_grau ON satisfacao(grau)
        """)
        
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_dia_semana ON satisfacao(dia_semana)
        """)
        
        conn.commit()
        conn.close()
        
        print("✅ Base de dados criada com sucesso!")
        print(f"📁 Arquivo: {DATABASE}")
        print("📊 Tabela 'satisfacao' criada com campos:")
        print("   - id (chave primária)")
        print("   - grau (Muito satisfeito, Satisfeito, Insatisfeito)")
        print("   - data (data do registo)")
        print("   - dia_semana (segunda a domingo)")
        print("   - hora (hora do registo)")
        print("   - criado_em (timestamp)")
        
    except sqlite3.Error as e:
        print(f"❌ Erro ao criar base de dados: {e}")

if __name__ == "__main__":
    init_database()


if __name__ == "__main__":
    init_database()

