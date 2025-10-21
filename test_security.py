#!/usr/bin/env python3
"""
Script de test de sécurité pour vérifier les corrections
"""

import re
import os

class SecurityTester:
    def __init__(self):
        self.tests_passed = 0
        self.tests_failed = 0
        self.vulnerabilities_found = []
    
    def test_sql_injection_protection(self):
        """Vérifie que les requêtes SQL sont paramétrées"""
        print("\n✅ Test 1: Protection contre l'injection SQL")
        
        with open('app.py', 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Recherche de patterns d'injection SQL vulnérables
        vulnerable_patterns = [
            r'f".*SELECT.*\{.*\}',  # f-string avec SELECT
            r'f".*INSERT.*\{.*\}',  # f-string avec INSERT
            r'f".*DELETE.*\{.*\}',  # f-string avec DELETE
            r'f".*UPDATE.*\{.*\}',  # f-string avec UPDATE
        ]
        
        found_vulnerabilities = False
        for pattern in vulnerable_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                found_vulnerabilities = True
                print(f"  ❌ VULNÉRABLE: Injection SQL possible")
                for match in matches:
                    print(f"     - {match[:50]}...")
        
        # Vérifier l'utilisation de requêtes paramétrées
        safe_patterns = re.findall(r'cursor\.execute\([^,]+,\s*\(', content)
        
        if not found_vulnerabilities and len(safe_patterns) > 0:
            print(f"  ✅ SÉCURISÉ: {len(safe_patterns)} requêtes paramétrées trouvées")
            self.tests_passed += 1
        else:
            print("  ❌ ÉCHEC: Vulnérabilités détectées")
            self.tests_failed += 1
            self.vulnerabilities_found.append("Injection SQL")
    
    def test_password_hashing(self):
        """Vérifie l'utilisation de bcrypt"""
        print("\n✅ Test 2: Hachage sécurisé des mots de passe")
        
        with open('app.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Vérifier MD5 (vulnérable)
        if 'hashlib.md5' in content:
            print("  ❌ VULNÉRABLE: Utilisation de MD5 détectée")
            self.tests_failed += 1
            self.vulnerabilities_found.append("Hachage faible MD5")
        # Vérifier bcrypt (sécurisé)
        elif 'bcrypt' in content and 'bcrypt.hashpw' in content:
            print("  ✅ SÉCURISÉ: Utilisation de bcrypt")
            self.tests_passed += 1
        else:
            print("  ⚠️  AVERTISSEMENT: Méthode de hachage non détectée")
            self.tests_failed += 1
    
    def test_xss_protection(self):
        """Vérifie l'absence de |safe dans les templates"""
        print("\n✅ Test 3: Protection contre XSS")
        
        vulnerable_templates = []
        for template in os.listdir('templates'):
            if template.endswith('.html'):
                with open(f'templates/{template}', 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Retirer les commentaires HTML
                    content_no_comments = re.sub(r'<!--.*?-->', '', content, flags=re.DOTALL)
                    if '|safe' in content_no_comments:
                        vulnerable_templates.append(template)
        
        if vulnerable_templates:
            print(f"  ❌ VULNÉRABLE: |safe détecté dans {len(vulnerable_templates)} template(s)")
            for t in vulnerable_templates:
                print(f"     - {t}")
            self.tests_failed += 1
            self.vulnerabilities_found.append("XSS")
        else:
            print("  ✅ SÉCURISÉ: Pas de |safe détecté")
            self.tests_passed += 1
    
    def test_csrf_protection(self):
        """Vérifie la protection CSRF"""
        print("\n✅ Test 4: Protection CSRF")
        
        with open('app.py', 'r', encoding='utf-8') as f:
            app_content = f.read()
        
        if 'CSRFProtect' not in app_content:
            print("  ❌ VULNÉRABLE: CSRFProtect non importé")
            self.tests_failed += 1
            self.vulnerabilities_found.append("CSRF")
            return
        
        # Vérifier les tokens CSRF dans les templates
        csrf_tokens_found = 0
        for template in os.listdir('templates'):
            if template.endswith('.html'):
                with open(f'templates/{template}', 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'csrf_token()' in content:
                        csrf_tokens_found += 1
        
        if csrf_tokens_found > 0:
            print(f"  ✅ SÉCURISÉ: Protection CSRF activée ({csrf_tokens_found} tokens trouvés)")
            self.tests_passed += 1
        else:
            print("  ⚠️  AVERTISSEMENT: Aucun token CSRF trouvé dans les templates")
            self.tests_failed += 1
    
    def test_secure_filename(self):
        """Vérifie l'utilisation de secure_filename"""
        print("\n✅ Test 5: Protection Path Traversal")
        
        with open('app.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        if 'secure_filename' in content:
            print("  ✅ SÉCURISÉ: Utilisation de secure_filename détectée")
            self.tests_passed += 1
        else:
            print("  ❌ VULNÉRABLE: secure_filename non utilisé")
            self.tests_failed += 1
            self.vulnerabilities_found.append("Path Traversal")
    
    def test_hardcoded_secrets(self):
        """Vérifie l'absence de secrets hardcodés"""
        print("\n✅ Test 6: Secrets hardcodés")
        
        with open('app.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Patterns de secrets hardcodés
        hardcoded_patterns = [
            (r'secret_key\s*=\s*[\'"](?!.*environ).*[\'"]', 'Secret key'),
            (r'password\s*=\s*[\'"]\w+[\'"]', 'Password'),
            (r'api[_-]?key\s*=\s*[\'"]\w+[\'"]', 'API Key'),
        ]
        
        found_secrets = []
        for pattern, name in hardcoded_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                # Vérifier si c'est bien hardcodé (pas depuis environ)
                for match in matches:
                    if 'environ' not in match and 'os.environ' not in match:
                        found_secrets.append(name)
        
        if found_secrets:
            print(f"  ❌ VULNÉRABLE: Secrets hardcodés détectés")
            for secret in set(found_secrets):
                print(f"     - {secret}")
            self.tests_failed += 1
            self.vulnerabilities_found.append("Secrets hardcodés")
        else:
            print("  ✅ SÉCURISÉ: Utilisation de variables d'environnement")
            self.tests_passed += 1
    
    def test_rate_limiting(self):
        """Vérifie la présence de rate limiting"""
        print("\n✅ Test 7: Rate Limiting")
        
        with open('app.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        if 'Limiter' in content and '@limiter.limit' in content:
            limits = re.findall(r'@limiter\.limit\(["\'](.+?)["\']\)', content)
            print(f"  ✅ SÉCURISÉ: Rate limiting activé ({len(limits)} routes protégées)")
            for limit in limits[:3]:  # Afficher les 3 premiers
                print(f"     - {limit}")
            self.tests_passed += 1
        else:
            print("  ❌ VULNÉRABLE: Pas de rate limiting")
            self.tests_failed += 1
            self.vulnerabilities_found.append("Rate Limiting")
    
    def test_idor_protection(self):
        """Vérifie la vérification de propriété des ressources"""
        print("\n✅ Test 8: Protection IDOR")
        
        with open('app.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        if 'check_resource_ownership' in content:
            print("  ✅ SÉCURISÉ: Fonction de vérification de propriété détectée")
            self.tests_passed += 1
        else:
            print("  ❌ VULNÉRABLE: Pas de vérification de propriété")
            self.tests_failed += 1
            self.vulnerabilities_found.append("IDOR")
    
    def test_dependencies(self):
        """Vérifie les dépendances"""
        print("\n✅ Test 9: Dépendances")
        
        with open('requirements.txt', 'r') as f:
            content = f.read()
        
        # Vérifier les versions obsolètes connues
        vulnerable_deps = [
            ('Flask==2.0.3', 'Flask vulnérable'),
            ('Pillow==8.3.2', 'Pillow vulnérable'),
            ('requests==2.25.1', 'Requests vulnérable'),
        ]
        
        found_vulnerable = []
        for dep, desc in vulnerable_deps:
            if dep in content:
                found_vulnerable.append(desc)
        
        if found_vulnerable:
            print(f"  ❌ VULNÉRABLE: Dépendances obsolètes détectées")
            for vuln in found_vulnerable:
                print(f"     - {vuln}")
            self.tests_failed += 1
            self.vulnerabilities_found.append("Dépendances obsolètes")
        else:
            print("  ✅ SÉCURISÉ: Pas de dépendances obsolètes connues")
            self.tests_passed += 1
    
    def test_session_security(self):
        """Vérifie la configuration sécurisée des sessions"""
        print("\n✅ Test 10: Sécurité des sessions")
        
        with open('app.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        session_flags = [
            ('SESSION_COOKIE_SECURE', 'Secure flag'),
            ('SESSION_COOKIE_HTTPONLY', 'HttpOnly flag'),
            ('SESSION_COOKIE_SAMESITE', 'SameSite flag'),
        ]
        
        found_flags = []
        missing_flags = []
        
        for flag, name in session_flags:
            if flag in content:
                found_flags.append(name)
            else:
                missing_flags.append(name)
        
        if len(found_flags) == len(session_flags):
            print(f"  ✅ SÉCURISÉ: Tous les flags de sécurité présents")
            for flag in found_flags:
                print(f"     - {flag}")
            self.tests_passed += 1
        else:
            print(f"  ❌ VULNÉRABLE: Flags manquants")
            for flag in missing_flags:
                print(f"     - {flag}")
            self.tests_failed += 1
            self.vulnerabilities_found.append("Sécurité des sessions")
    
    def run_all_tests(self):
        """Exécute tous les tests"""
        print("="*60)
        print("  TEST DE SÉCURITÉ - VERSION SÉCURISÉE")
        print("="*60)
        
        self.test_sql_injection_protection()
        self.test_password_hashing()
        self.test_xss_protection()
        self.test_csrf_protection()
        self.test_secure_filename()
        self.test_hardcoded_secrets()
        self.test_rate_limiting()
        self.test_idor_protection()
        self.test_dependencies()
        self.test_session_security()
        
        # Résumé
        print("\n" + "="*60)
        print("  RÉSUMÉ")
        print("="*60)
        print(f"\n  Tests réussis: {self.tests_passed} ✅")
        print(f"  Tests échoués: {self.tests_failed} ❌")
        
        if self.vulnerabilities_found:
            print("\n  Vulnérabilités détectées:")
            for vuln in self.vulnerabilities_found:
                print(f"    - {vuln}")
        
        print("\n" + "="*60)
        
        if self.tests_failed == 0:
            print("  🎉 SUCCÈS: Toutes les vulnérabilités ont été corrigées!")
            print("="*60)
            return True
        else:
            print("  ⚠️  ATTENTION: Certaines vulnérabilités sont encore présentes")
            print("="*60)
            return False

if __name__ == '__main__':
    tester = SecurityTester()
    success = tester.run_all_tests()
    exit(0 if success else 1)
